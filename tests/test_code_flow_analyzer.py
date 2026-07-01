"""
Test code flow analyzer functionality.
"""

import pytest
from winmerge_ai_exporter.code_flow_analyzer import (
    CodeFlowAnalyzer,
    analyze_code_flow,
    ControlFlowType,
)


class TestCodeFlowAnalyzer:
    """Tests for CodeFlowAnalyzer."""
    
    def test_detect_if_else(self):
        """Test if/else detection."""
        code = """
        if (x > 0) {
            doSomething();
        } else {
            doOther();
        }
        """
        analyzer = CodeFlowAnalyzer(code)
        assert len(analyzer.flows) > 0
        if_flows = [f for f in analyzer.flows if f.type == ControlFlowType.IF_ELSE]
        assert len(if_flows) > 0
    
    def test_detect_switch_case(self):
        """Test switch/case detection."""
        code = """
        switch (status) {
            case "active":
                handle_active();
                break;
            case "inactive":
                handle_inactive();
                break;
            default:
                handle_default();
        }
        """
        analyzer = CodeFlowAnalyzer(code)
        switch_flows = [f for f in analyzer.flows if f.type == ControlFlowType.SWITCH_CASE]
        assert len(switch_flows) > 0
    
    def test_detect_loop(self):
        """Test loop detection."""
        code = """
        for (int i = 0; i < 10; i++) {
            process(i);
        }
        
        while (count > 0) {
            decrement();
        }
        """
        analyzer = CodeFlowAnalyzer(code)
        loops = [f for f in analyzer.flows if f.type == ControlFlowType.LOOP]
        assert len(loops) >= 2
    
    def test_detect_function_call(self):
        """Test function call detection."""
        code = """
        validate_input(data);
        processPayment(amount);
        user.updateProfile(info);
        """
        analyzer = CodeFlowAnalyzer(code)
        calls = [f for f in analyzer.flows if f.type == ControlFlowType.FUNCTION_CALL]
        assert len(calls) >= 3
    
    def test_detect_event_trigger(self):
        """Test event trigger detection."""
        code = """
        addEventListener('click', handler);
        emitter.emit('data_changed');
        element.on('hover', callback);
        subject.subscribe(observer);
        dispatch(action);
        """
        analyzer = CodeFlowAnalyzer(code)
        events = [f for f in analyzer.flows if f.type == ControlFlowType.EVENT_TRIGGER]
        assert len(events) >= 3
    
    def test_detect_try_catch(self):
        """Test try/catch detection."""
        code = """
        try {
            riskyOperation();
        } catch (Exception e) {
            handleError(e);
        } finally {
            cleanup();
        }
        """
        analyzer = CodeFlowAnalyzer(code)
        try_flows = [f for f in analyzer.flows if f.type == ControlFlowType.TRY_CATCH]
        # Should detect at least try block (catch and finally may not be on separate lines)
        assert len(try_flows) >= 1
    
    def test_generate_flowchart(self):
        """Test flowchart generation."""
        code = """
        if (valid) {
            save();
        } else {
            error();
        }
        """
        analyzer = CodeFlowAnalyzer(code)
        flowchart = analyzer.generate_mermaid_flowchart()
        
        assert "graph TD" in flowchart
        assert "Start" in flowchart
        assert "End" in flowchart
        assert "-->" in flowchart
    
    def test_generate_sequence(self):
        """Test sequence diagram generation."""
        code = """
        validate_input();
        emit('started');
        process_data();
        """
        analyzer = CodeFlowAnalyzer(code)
        sequence = analyzer.generate_mermaid_sequence()
        
        assert "sequenceDiagram" in sequence
        assert "Main" in sequence
        assert "System" in sequence
    
    def test_analyze_code_flow_helper(self):
        """Test convenience function."""
        code = "if (x > 0) { foo(); }"
        
        flowchart = analyze_code_flow(code, diagram_type="flowchart")
        assert "graph TD" in flowchart
        
        sequence = analyze_code_flow(code, diagram_type="sequence")
        assert "sequenceDiagram" in sequence
        
        state = analyze_code_flow(code, diagram_type="state")
        assert "stateDiagram" in state
    
    def test_complex_code(self):
        """Test with more complex code."""
        code = """
        def process_payment(amount, card):
            if amount > 0:
                if card.validate():
                    authorize_payment(amount)
                else:
                    emit('validation_failed')
            else:
                raise ValueError('Invalid amount')
            
            emit('payment_processed')
        """
        analyzer = CodeFlowAnalyzer(code)
        
        assert len(analyzer.flows) > 5
        
        flowchart = analyzer.generate_mermaid_flowchart()
        assert len(flowchart) > 50  # Should have substantial content
    
    def test_empty_code(self):
        """Test with empty code."""
        code = "# just comments\n# nothing else"
        analyzer = CodeFlowAnalyzer(code)
        
        assert len(analyzer.flows) == 0
        
        flowchart = analyzer.generate_mermaid_flowchart()
        assert "No Control Flow Detected" in flowchart
    
    def test_linker_map_file_is_filtered(self):
        """
        Regression test: Keil/ARM linker .map file content must not produce
        meaningless flow nodes (e.g. single-letter "o()" calls scraped from
        "common.o(i.Func) refers to..." cross-reference lines).
        """
        map_content = """
        Section Cross References

            common.o(i.I2C_KB_Refresh) refers to sn34f28x_hal_i2c.o(i.HAL_I2C_Master_Transmit) for HAL_I2C_Master_Transmit
            common.o(i.I2C_KB_Refresh) refers to sn34f28x_hal_i2c.o(i.HAL_I2C_Master_Transmit_IT) for HAL_I2C_Master_Transmit_IT
            kb_function.o(i.KB_BufferGameModeKey) refers to led_ramsetting.o(.data) for strGameProfile
            kb_function.o(i.KB_BufferModifierKey) refers to kb_ramsetting.o(.bss) for b_aryKB_Usage

            Execution Region RW_IRAM1 (Exec base: 0x20000000, Load base: 0x0000bd44, Size: 0x00005498, Max: 0x00028000)

                43482       2728       4324       1120      20524     728194   Object Totals
                44132       2800       4324       1132      20524     696627   Grand Totals
                44132       2800       4324        496      20524     696627   ELF Image Totals (compressed)
        """
        analyzer = CodeFlowAnalyzer(map_content)
        assert len(analyzer.flows) == 0
        
        flowchart = analyzer.generate_mermaid_flowchart()
        assert "No Control Flow Detected" in flowchart
        # Must not contain the meaningless single-letter call nodes
        assert 'Call: o()' not in flowchart
        assert 'Call: l()' not in flowchart
    
    def test_method_call_with_object_prefix(self):
        """Object.method() calls should still be detected (not just bare calls)."""
        code = "user.updateProfile(info);\nsession.validate(token);"
        analyzer = CodeFlowAnalyzer(code)
        calls = [f for f in analyzer.flows if f.type == ControlFlowType.FUNCTION_CALL]
        names = [c.name for c in calls]
        
        assert any("updateProfile" in n for n in names)
        assert any("validate" in n for n in names)
    
    def test_single_letter_dotted_fragment_rejected(self):
        """
        A bare 'x.o(...)' or 'x.l(...)' fragment (as seen in linker maps)
        must not be mistaken for a function call, even outside a full
        linker-map context.
        """
        code = "common.o(i.SomeFunc)\nkb_table.l(.constdata)"
        analyzer = CodeFlowAnalyzer(code)
        calls = [f for f in analyzer.flows if f.type == ControlFlowType.FUNCTION_CALL]
        names = [c.name for c in calls]
        
        assert "Call: o()" not in names
        assert "Call: l()" not in names
    
    def test_duplicate_calls_are_deduplicated(self):
        """Identical repeated calls should only produce one flow node."""
        code = "\n".join(["validate_input(data);"] * 10)
        analyzer = CodeFlowAnalyzer(code)
        calls = [f for f in analyzer.flows if f.type == ControlFlowType.FUNCTION_CALL]
        
        assert len(calls) == 1
    
    def test_node_cap_limits_large_diagrams(self):
        """Diagrams should be capped at _MAX_DIAGRAM_NODES distinct nodes."""
        # Generate more unique calls than the cap allows
        code = "\n".join([f"do_action_{i}();" for i in range(50)])
        analyzer = CodeFlowAnalyzer(code)
        
        assert len(analyzer.flows) == 50  # all detected
        
        flowchart = analyzer.generate_mermaid_flowchart()
        # Rendered flowchart should mention the cap was hit
        assert "more not shown" in flowchart


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
