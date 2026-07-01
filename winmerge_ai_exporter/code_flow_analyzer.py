"""
code_flow_analyzer.py — Analyzes code structure and generates Mermaid flowchart diagrams.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Detects control flow patterns in code and generates Mermaid diagrams:
- if/else/else if statements
- switch/case statements
- function calls and callbacks
- event listeners/triggers
- loops (for, while)
- try/catch blocks
- return statements

Supports multiple languages: C/C++/Python/Java/JavaScript/TypeScript
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ControlFlowType(Enum):
    """Types of control flow structures."""
    IF_ELSE = "if_else"
    SWITCH_CASE = "switch_case"
    LOOP = "loop"
    FUNCTION_CALL = "function_call"
    EVENT_TRIGGER = "event_trigger"
    TRY_CATCH = "try_catch"
    RETURN = "return"
    CONDITION = "condition"


@dataclass
class ControlFlowBlock:
    """Represents a control flow block in code."""
    type: ControlFlowType
    name: str
    condition: Optional[str] = None
    true_branch: str = "true"
    false_branch: str = "false"
    cases: dict = field(default_factory=dict)  # for switch
    children: list = field(default_factory=list)
    line_number: int = 0

    def to_mermaid_node(self) -> str:
        """Convert to Mermaid node syntax."""
        node_id = f"node_{self.line_number}_{id(self)}"
        
        if self.type == ControlFlowType.IF_ELSE:
            return f"{node_id}{{{{Decision: {self.name}}}}}"
        elif self.type == ControlFlowType.SWITCH_CASE:
            return f"{node_id}{{{{Switch: {self.name}}}}}"
        elif self.type == ControlFlowType.LOOP:
            return f"{node_id}([Loop: {self.name}])"
        elif self.type == ControlFlowType.FUNCTION_CALL:
            return f"{node_id}[\"{self.name}\"]"
        elif self.type == ControlFlowType.EVENT_TRIGGER:
            return f"{node_id}(\"Event: {self.name}\")"
        elif self.type == ControlFlowType.TRY_CATCH:
            return f"{node_id}{{{{Try/Catch: {self.name}}}}}"
        else:
            return f"{node_id}[\"{self.name}\"]"


class CodeFlowAnalyzer:
    """Analyzes code and generates Mermaid flowchart diagrams."""
    
    # Minimum valid identifier length for a function call match.
    # Filters out linker-map noise like "common.o(i.Func)" being mis-split into "o(".
    _MIN_FUNC_NAME_LEN = 3
    
    # Identifiers that are language keywords, not function calls.
    _CONTROL_KEYWORDS = {
        "if", "for", "while", "switch", "catch", "return", "sizeof",
        "else", "do", "try", "finally", "new", "delete", "typeof",
        "instanceof", "in", "of", "function", "async", "await",
    }
    
    # Lines matching these patterns are linker/build-tool artifacts, not source
    # code, and should be skipped entirely (common in .map files exported
    # from Keil/ARM/GCC linkers, or compiler diagnostic output).
    _NON_SOURCE_LINE_PATTERNS = [
        re.compile(r'\brefers to\b'),                       # "x.o(...) refers to y.o(...)"
        re.compile(r'^\s*[\w.]+\.o\([^)]*\)'),               # "common.o(i.Foo)" cross-ref lines
        re.compile(r'^\s*Execution Region\b'),               # linker region summary
        re.compile(r'\b(Object|Grand|ELF Image|ROM|RAM)\s+Totals\b'),  # size-report tables
        re.compile(r'^\s*Load Region\b'),
        re.compile(r'^\s*\*{3,}'),                           # "*** ..." banner lines
        re.compile(r'^\s*={3,}'),                            # "===..." separator lines
        re.compile(r'^\s*-{3,}'),                            # "---..." separator lines
        re.compile(r'^\s*Section Cross References\b'),
        re.compile(r'^\s*(Code|Data|RO|RW|ZI)\s+Size\b'),    # size-summary header rows
    ]
    
    def __init__(self, code: str, language: str = "auto"):
        """
        Initialize analyzer.
        
        Args:
            code: Source code to analyze
            language: Programming language (auto, c, cpp, python, java, js, ts)
        """
        self.code = code
        self.language = language
        self.flows: list[ControlFlowBlock] = []
        self._seen_signatures: set[str] = set()  # de-dup identical flow nodes
        self._analyze_code()
    
    def _is_non_source_line(self, line: str) -> bool:
        """
        Return True if this line looks like linker/build-tool output rather
        than actual source code (e.g. a WinMerge diff of a .map file).
        """
        return any(pat.search(line) for pat in self._NON_SOURCE_LINE_PATTERNS)
    
    def _looks_like_source_code(self) -> bool:
        """
        Heuristic check: does the overall input look like real source code,
        or does it look like a linker map / build report?
        
        If more than a third of non-blank lines are linker-map artifacts,
        we treat the whole input as non-source and skip flow analysis,
        rather than emitting dozens of meaningless single-letter "function
        call" nodes scraped from cross-reference noise.
        """
        lines = [l for l in self.code.split('\n') if l.strip()]
        if not lines:
            return False
        
        noise_count = sum(1 for l in lines if self._is_non_source_line(l))
        return (noise_count / len(lines)) < 0.34
    
    def _dedupe_key(self, flow_type: "ControlFlowType", name: str) -> str:
        """Build a de-duplication key for a flow node."""
        return f"{flow_type.value}:{name}"
    
    def _add_flow(self, block: "ControlFlowBlock") -> None:
        """Add a flow block, skipping exact duplicates already recorded."""
        key = self._dedupe_key(block.type, block.name)
        if key in self._seen_signatures:
            return
        self._seen_signatures.add(key)
        self.flows.append(block)
    
    def _analyze_code(self):
        """Analyze code and extract control flow structures."""
        # Bail out early if this doesn't look like source code at all
        # (e.g. a linker .map file, build log, or size report).
        if not self._looks_like_source_code():
            return
        
        lines = self.code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue
            
            # Skip linker-map / build-report artifact lines
            if self._is_non_source_line(stripped):
                continue
            
            # Detect control flow patterns
            self._detect_if_else(stripped, line_num)
            self._detect_switch(stripped, line_num)
            self._detect_loop(stripped, line_num)
            self._detect_try_catch(stripped, line_num)
            
            # Event triggers take priority over generic function calls on
            # the same line (e.g. emit("x") is one semantic action, not two)
            if not self._detect_event(stripped, line_num):
                self._detect_function_call(stripped, line_num)
    
    def _detect_if_else(self, line: str, line_num: int):
        """Detect if/else statements."""
        # Match: if (...), if(...) {
        if_match = re.match(r'^if\s*\((.*?)\)', line)
        if if_match:
            condition = if_match.group(1).strip()
            if condition:
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.IF_ELSE,
                    name=f"if ({condition[:40]}...)" if len(condition) > 40 else f"if ({condition})",
                    condition=condition,
                    line_number=line_num
                ))
            return
        
        # Match: else if
        elif_match = re.match(r'^else\s+if\s*\((.*?)\)', line)
        if elif_match:
            condition = elif_match.group(1).strip()
            if condition:
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.IF_ELSE,
                    name=f"else if ({condition[:40]}...)" if len(condition) > 40 else f"else if ({condition})",
                    condition=condition,
                    line_number=line_num
                ))
            return
        
        # Match: else (bare, not "else if")
        if re.match(r'^else\s*[{:]?\s*$', line):
            self._add_flow(ControlFlowBlock(
                type=ControlFlowType.IF_ELSE,
                name="else",
                true_branch="else",
                line_number=line_num
            ))
    
    def _detect_switch(self, line: str, line_num: int):
        """Detect switch/case statements."""
        switch_match = re.match(r'^switch\s*\((.*?)\)', line)
        if switch_match:
            var = switch_match.group(1).strip()
            if var:
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.SWITCH_CASE,
                    name=f"switch ({var})",
                    condition=var,
                    line_number=line_num
                ))
            return
        
        # Match: case <value>:
        case_match = re.match(r'^case\s+([^:]+):', line)
        if case_match:
            case_val = case_match.group(1).strip()
            if case_val:
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.SWITCH_CASE,
                    name=f"case {case_val}",
                    true_branch=case_val,
                    line_number=line_num
                ))
            return
        
        if re.match(r'^default\s*:', line):
            self._add_flow(ControlFlowBlock(
                type=ControlFlowType.SWITCH_CASE,
                name="default",
                true_branch="default",
                line_number=line_num
            ))
    
    def _detect_loop(self, line: str, line_num: int):
        """Detect loop statements (for, while)."""
        # for loop
        for_match = re.match(r'^for\s*\((.*?)\)', line)
        if for_match:
            condition = for_match.group(1).strip()
            if condition:
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.LOOP,
                    name=f"for ({condition[:40]}...)" if len(condition) > 40 else f"for ({condition})",
                    condition=condition,
                    line_number=line_num
                ))
            return
        
        # while loop
        while_match = re.match(r'^while\s*\((.*?)\)', line)
        if while_match:
            condition = while_match.group(1).strip()
            if condition:
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.LOOP,
                    name=f"while ({condition[:40]}...)" if len(condition) > 40 else f"while ({condition})",
                    condition=condition,
                    line_number=line_num
                ))
            return
        
        # foreach/for-in loop
        foreach_match = re.match(r'^for(?:each)?\s+\(.*?\s+(?:in|:)\s+(.*?)\)', line)
        if foreach_match:
            var = foreach_match.group(1).strip()
            if var:
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.LOOP,
                    name=f"foreach ({var})",
                    condition=var,
                    line_number=line_num
                ))
    
    def _detect_function_call(self, line: str, line_num: int):
        """
        Detect function calls.
        
        Deliberately conservative to avoid false positives from non-code
        text (e.g. linker cross-reference lines like "x.o(i.Func)" which
        would otherwise be mis-parsed into a meaningless "o()" call).
        """
        # Match identifier(s) immediately followed by "(". This allows both
        # bare calls (foo()) and method calls (obj.method()) — the minimum
        # length requirement on the identifier itself (3+ chars) is what
        # filters out linker-map noise like "common.o(" or "kb_table.l(",
        # since those fragments are exactly 1 character before the paren.
        func_match = re.search(
            r'\b([A-Za-z_][A-Za-z0-9_]{2,})\s*\(',
            line
        )
        if not func_match:
            return
        
        func_name = func_match.group(1)
        
        # Skip control-flow keywords (already handled by dedicated detectors)
        if func_name.lower() in self._CONTROL_KEYWORDS:
            return
        
        # Skip if too short to be a meaningful identifier
        if len(func_name) < self._MIN_FUNC_NAME_LEN:
            return
        
        # Skip ALL-CAPS single tokens that are more likely macros/constants
        # used as casts, e.g. "(uint8_t)" — but allow ALL_CAPS_WITH_UNDERSCORE
        # function-like macros since those usually represent real actions.
        if func_name.isupper() and '_' not in func_name:
            return
        
        self._add_flow(ControlFlowBlock(
            type=ControlFlowType.FUNCTION_CALL,
            name=f"Call: {func_name}()",
            line_number=line_num
        ))
    
    def _detect_event(self, line: str, line_num: int) -> bool:
        """
        Detect event listeners/triggers.
        
        Returns:
            True if an event pattern matched this line, False otherwise.
        """
        # Match: addEventListener, on, emit, trigger, subscribe, etc
        event_patterns = [
            r'addEventListener\s*\(\s*["\'](\w+)["\']',
            r'\.on\s*\(\s*["\'](\w+)["\']',
            r'\bemit\s*\(\s*["\'](\w+)["\']',
            r'\btrigger\s*\(\s*["\'](\w+)["\']',
            r'\bsubscribe\s*\(\s*["\'](\w+)["\']',
            r'\bdispatch\s*\(\s*(\w+)',
        ]
        
        for pattern in event_patterns:
            event_match = re.search(pattern, line)
            if event_match:
                event_name = event_match.group(1)
                action = "Listen" if "addEventListener" in pattern or ".on" in pattern or "subscribe" in pattern else "Emit"
                self._add_flow(ControlFlowBlock(
                    type=ControlFlowType.EVENT_TRIGGER,
                    name=f"{action}: {event_name}",
                    condition=event_name,
                    line_number=line_num
                ))
                return True
        return False
    
    def _detect_try_catch(self, line: str, line_num: int):
        """Detect try/catch blocks."""
        if re.match(r'^try\s*[{:]?\s*$', line):
            self._add_flow(ControlFlowBlock(
                type=ControlFlowType.TRY_CATCH,
                name="try",
                true_branch="try",
                line_number=line_num
            ))
            return
        
        catch_match = re.match(r'^catch\s*\((.*?)\)', line)
        if catch_match:
            exception = catch_match.group(1).strip()
            self._add_flow(ControlFlowBlock(
                type=ControlFlowType.TRY_CATCH,
                name=f"catch ({exception})" if exception else "catch",
                condition=exception,
                line_number=line_num
            ))
            return
        
        if re.match(r'^finally\s*[{:]?\s*$', line):
            self._add_flow(ControlFlowBlock(
                type=ControlFlowType.TRY_CATCH,
                name="finally",
                true_branch="finally",
                line_number=line_num
            ))
    
    # Cap the number of nodes rendered in a single diagram. Large diffs can
    # contain hundreds of distinct calls/conditions; beyond this point the
    # diagram becomes unreadable noise rather than a useful visualization.
    _MAX_DIAGRAM_NODES = 25
    
    @staticmethod
    def _escape_label(text: str) -> str:
        """Escape characters that break Mermaid node label syntax."""
        return (
            text.replace('"', "'")
                .replace("{", "(")
                .replace("}", ")")
                .replace("[", "(")
                .replace("]", ")")
                .replace("|", "/")
        )
    
    def generate_mermaid_flowchart(self) -> str:
        """Generate Mermaid flowchart diagram."""
        if not self.flows:
            return "graph TD\n    Start([Start])\n    Start --> End([No Control Flow Detected])"
        
        flows = self.flows[: self._MAX_DIAGRAM_NODES]
        truncated = len(self.flows) > self._MAX_DIAGRAM_NODES
        
        lines = ["graph TD"]
        
        # Add start node
        lines.append("    Start([Start])")
        
        # Add flow nodes
        node_ids = {}
        for i, flow in enumerate(flows):
            node_id = f"flow_{i}"
            node_ids[i] = node_id
            label = self._escape_label(flow.name)
            
            if flow.type == ControlFlowType.IF_ELSE:
                lines.append(f"    {node_id}{{{label}}}")
            elif flow.type == ControlFlowType.SWITCH_CASE:
                lines.append(f"    {node_id}{{{label}}}")
            elif flow.type == ControlFlowType.LOOP:
                lines.append(f"    {node_id}([{label}])")
            elif flow.type == ControlFlowType.EVENT_TRIGGER:
                lines.append(f"    {node_id}(\"{label}\")")
            elif flow.type == ControlFlowType.FUNCTION_CALL:
                lines.append(f"    {node_id}[\"{label}\"]")
            elif flow.type == ControlFlowType.TRY_CATCH:
                lines.append(f"    {node_id}{{{label}}}")
            else:
                lines.append(f"    {node_id}[\"{label}\"]")
        
        # Add connections
        lines.append("    Start --> flow_0")
        
        for i in range(len(flows) - 1):
            curr_id = node_ids[i]
            next_id = node_ids[i + 1]
            lines.append(f"    {curr_id} --> {next_id}")
        
        # Add end node
        last_id = node_ids[len(flows) - 1] if flows else "Start"
        if truncated:
            lines.append(
                f"    flow_end([End — {len(self.flows) - self._MAX_DIAGRAM_NODES} more not shown])"
            )
        else:
            lines.append("    flow_end([End])")
        lines.append(f"    {last_id} --> flow_end")
        
        return "\n".join(lines)
    
    def generate_mermaid_sequence(self) -> str:
        """Generate Mermaid sequence diagram (for event-driven flows)."""
        event_flows = [f for f in self.flows if f.type == ControlFlowType.EVENT_TRIGGER]
        func_flows = [f for f in self.flows if f.type == ControlFlowType.FUNCTION_CALL]
        
        if not event_flows and not func_flows:
            return "sequenceDiagram\n    Note over Main,System: No event or function calls detected"
        
        relevant = (event_flows + func_flows)[: self._MAX_DIAGRAM_NODES]
        
        lines = ["sequenceDiagram", "    actor Main", "    participant System"]
        
        for flow in relevant:
            if flow.type == ControlFlowType.EVENT_TRIGGER:
                action = "Emit" if "Emit" in flow.name else "Listen"
                event_name = self._escape_label(flow.condition or flow.name)
                if action == "Emit":
                    lines.append(f"    Main->>System: emit({event_name})")
                else:
                    lines.append(f"    System->>Main: on({event_name})")
            elif flow.type == ControlFlowType.FUNCTION_CALL:
                func_name = self._escape_label(flow.name.replace("Call: ", "").replace("()", ""))
                lines.append(f"    Main->>System: {func_name}()")
        
        return "\n".join(lines)
    
    def generate_mermaid_state(self) -> str:
        """Generate Mermaid state diagram (for state transitions)."""
        if_flows = [f for f in self.flows if f.type == ControlFlowType.IF_ELSE]
        switch_flows = [f for f in self.flows if f.type == ControlFlowType.SWITCH_CASE]
        
        if not if_flows and not switch_flows:
            return "stateDiagram-v2\n    [*] --> Idle\n    Idle --> [*]"
        
        relevant = (if_flows + switch_flows)[: self._MAX_DIAGRAM_NODES]
        
        lines = ["stateDiagram-v2", "    [*] --> Start"]
        
        for i, flow in enumerate(relevant):
            state_name = f"State_{i}"
            label = self._escape_label(flow.name)
            
            if flow.type == ControlFlowType.IF_ELSE:
                lines.append(f"    Start --> {state_name}: {label}")
                lines.append(f"    {state_name} --> End: completed")
            elif flow.type == ControlFlowType.SWITCH_CASE:
                lines.append(f"    {state_name} --> End: {label}")
        
        lines.append("    End --> [*]")
        return "\n".join(lines)


# Helper function
def analyze_code_flow(code: str, language: str = "auto", diagram_type: str = "flowchart") -> str:
    """
    Convenience function to analyze code and generate Mermaid diagram.
    
    Args:
        code: Source code to analyze
        language: Programming language
        diagram_type: Type of diagram - 'flowchart', 'sequence', or 'state'
    
    Returns:
        Mermaid diagram code as string
    """
    analyzer = CodeFlowAnalyzer(code, language)
    
    if diagram_type == "sequence":
        return analyzer.generate_mermaid_sequence()
    elif diagram_type == "state":
        return analyzer.generate_mermaid_state()
    else:  # flowchart (default)
        return analyzer.generate_mermaid_flowchart()
