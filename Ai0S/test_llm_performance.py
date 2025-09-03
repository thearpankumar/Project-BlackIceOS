#!/usr/bin/env python3
"""
Standalone LLM Performance Tester
Tests raw Gemini 2.5 Pro response times with actual prompts from our system.
This isolates LLM performance from system complexity to identify bottlenecks.
"""

import asyncio
import time
import json
import os
import sys
from typing import Dict, Any

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import google.generativeai as genai
from src.Ai0S.config.settings import get_settings


class LLMPerformanceTester:
    """Test raw LLM performance with actual prompts."""
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_gemini()
        self.test_results = []
    
    def _setup_gemini(self):
        """Initialize Gemini 2.5 Flash."""
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        self.gemini = genai.GenerativeModel("gemini-2.5-flash")
        print(f"✅ Initialized Gemini 2.5 Flash")
    
    async def test_analyze_command_intent(self, user_command: str) -> Dict[str, Any]:
        """Test the analyze_command_intent prompt."""
        
        print(f"\n🔍 Testing analyze_command_intent with: '{user_command}'")
        
        # Exact prompt from our system
        intent_prompt = f"""
        Analyze this user command and extract structured information:
        
        USER COMMAND: {user_command}
        
        CONTEXT:
        - Current Applications: []
        - Recent Actions: []
        - Available Capabilities: ['browser_control', 'file_operations', 'system_commands']
        
        Return JSON analysis:
        {{
            "intent_type": "web_navigation|file_operation|application_control|system_command|complex_task",
            "primary_action": "main action to perform",
            "target_application": "target app or null",
            "parameters": {{"key": "extracted parameters"}},
            "complexity": "simple|medium|complex",
            "requires_confirmation": true/false,
            "estimated_steps": 3,
            "confidence": 0.95,
            "interpretation": "human readable interpretation"
        }}
        
        Return valid JSON only.
        """
        
        start_time = time.time()
        
        try:
            response = await asyncio.to_thread(
                self.gemini.generate_content,
                intent_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=1024
                )
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse response with error handling
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError as json_error:
                print(f"  ⚠️  JSON Parse Error: {json_error}")
                print(f"  📄 Raw response: {response.text[:200]}...")
                # Try to extract JSON from response if it's embedded
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        print(f"  ✅ Recovered JSON from response")
                    except:
                        result = {"error": "malformed_json", "raw_response": response.text}
                else:
                    result = {"error": "no_json_found", "raw_response": response.text}
            
            print(f"  ⏱️  Duration: {duration:.2f} seconds")
            print(f"  📄 Response length: {len(response.text)} chars")
            
            if "error" not in result:
                print(f"  🎯 Intent type: {result.get('intent_type', 'unknown')}")
                print(f"  📊 Estimated steps: {result.get('estimated_steps', 'unknown')}")
                print(f"  🔢 Confidence: {result.get('confidence', 'unknown')}")
            else:
                print(f"  ❌ Response error: {result.get('error', 'unknown')}")
            
            return {
                "success": True,
                "duration": duration,
                "response": result,
                "response_size": len(response.text)
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            # Handle rate limiting
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"  🚫 Rate limited after {duration:.2f} seconds - waiting 60 seconds...")
                await asyncio.sleep(60)  # Wait longer to be safe
                return {
                    "success": False,
                    "duration": duration,
                    "error": f"Rate limited: {str(e)}"
                }
            
            print(f"  ❌ Failed after {duration:.2f} seconds: {e}")
            return {
                "success": False,
                "duration": duration,
                "error": str(e)
            }
    
    async def test_create_execution_plan(self, user_command: str) -> Dict[str, Any]:
        """Test the create_execution_plan prompt."""
        
        print(f"\n🎯 Testing create_execution_plan with: '{user_command}'")
        
        # Exact prompt from our system
        planning_prompt = f"""
        You are an intelligent OS control agent. Generate a detailed execution plan for the user's request.
        
        USER REQUEST: {user_command}
        
        CURRENT SCREEN STATE:
        Not available
        
        SYSTEM CONTEXT:
        - OS: Linux
        - Display Server: X11
        - Capabilities: ['browser_control', 'file_operations', 'system_commands']
        
        Generate a JSON execution plan with this structure:
        {{
            "task_id": "unique_task_id",
            "user_intent": "{user_command}",
            "total_steps": 5,
            "estimated_time": 30.0,
            "steps": [
                {{
                    "step_id": "step_1",
                    "order": 1,
                    "description": "Clear description of what this step does",
                    "action_type": "click|type|command|wait|verify",
                    "target": "element description or command",
                    "parameters": {{"key": "value"}},
                    "pre_conditions": ["what must be true before this step"],
                    "post_conditions": ["what should be true after this step"],
                    "timeout": 10.0,
                    "retry_strategy": "retry_on_failure|wait_and_retry|fallback",
                    "fallback_step_id": "alternative_step_id",
                    "expected_screen_change": "description of expected change"
                }}
            ],
            "contingency_plans": {{
                "error_recovery": [
                    {{"step_id": "error_step_1", "description": "Handle error case"}}
                ],
                "unexpected_popup": [
                    {{"step_id": "popup_step_1", "description": "Handle popup"}}
                ]
            }},
            "success_criteria": "How to determine if the task succeeded",
            "confidence_score": 0.9
        }}
        
        PLANNING GUIDELINES:
        1. Break complex tasks into atomic, executable steps
        2. Include error handling and fallback strategies
        3. Consider the current screen state when planning
        4. Generate OS-appropriate commands dynamically
        5. Include verification steps to ensure success
        6. Plan for unexpected UI elements (popups, dialogs)
        7. Estimate realistic timeouts for each step
        8. Provide clear success criteria
        
        Return valid JSON only.
        """
        
        start_time = time.time()
        
        try:
            response = await asyncio.to_thread(
                self.gemini.generate_content,
                f"You are an expert OS automation agent that generates dynamic execution plans.\n\n{planning_prompt}",
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=4096
                )
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse response with error handling
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError as json_error:
                print(f"  ⚠️  JSON Parse Error: {json_error}")
                print(f"  📄 Raw response: {response.text[:200]}...")
                # Try to extract JSON from response if it's embedded
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        print(f"  ✅ Recovered JSON from response")
                    except:
                        result = {"error": "malformed_json", "raw_response": response.text}
                else:
                    result = {"error": "no_json_found", "raw_response": response.text}
            
            print(f"  ⏱️  Duration: {duration:.2f} seconds")
            print(f"  📄 Response length: {len(response.text)} chars")
            
            if "error" not in result:
                print(f"  📋 Total steps: {result.get('total_steps', 'unknown')}")
                print(f"  ⌚ Estimated time: {result.get('estimated_time', 'unknown')}s")
                print(f"  🔢 Confidence: {result.get('confidence_score', 'unknown')}")
                
                # Show first few steps
                steps = result.get('steps', [])
                for i, step in enumerate(steps[:3]):
                    print(f"    Step {i+1}: {step.get('description', 'No description')}")
                
                if len(steps) > 3:
                    print(f"    ... and {len(steps) - 3} more steps")
            else:
                print(f"  ❌ Response error: {result.get('error', 'unknown')}")
                steps = []
            
            return {
                "success": True,
                "duration": duration,
                "response": result,
                "response_size": len(response.text),
                "steps_generated": len(steps)
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            # Handle rate limiting
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"  🚫 Rate limited after {duration:.2f} seconds - waiting 60 seconds...")
                await asyncio.sleep(60)  # Wait longer to be safe
                return {
                    "success": False,
                    "duration": duration,
                    "error": f"Rate limited: {str(e)}"
                }
            
            print(f"  ❌ Failed after {duration:.2f} seconds: {e}")
            return {
                "success": False,
                "duration": duration,
                "error": str(e)
            }
    
    async def run_comprehensive_test(self):
        """Run comprehensive LLM performance tests."""
        
        print("🚀 Starting Comprehensive LLM Performance Test")
        print("=" * 60)
        
        # Test commands of varying complexity
        test_commands = [
            "open google chrome and go to yt",
            "take a screenshot", 
            "create a new folder called test",
            "open chrome, go to youtube, search for python tutorials, play the first video"
        ]
        
        total_start = time.time()
        
        for command in test_commands:
            print(f"\n📝 Testing command: '{command}'")
            print("-" * 50)
            
            # Test analyze_command_intent
            intent_result = await self.test_analyze_command_intent(command)
            self.test_results.append({
                "command": command,
                "test_type": "analyze_command_intent",
                **intent_result
            })
            
            # Wait between API calls to avoid rate limiting
            print(f"  ⏳ Waiting 30 seconds before next API call to avoid rate limits...")
            await asyncio.sleep(30)
            
            # Test create_execution_plan  
            plan_result = await self.test_create_execution_plan(command)
            self.test_results.append({
                "command": command,
                "test_type": "create_execution_plan",
                **plan_result
            })
            
            # Calculate combined time
            if intent_result["success"] and plan_result["success"]:
                combined_time = intent_result["duration"] + plan_result["duration"]
                print(f"  🔄 Combined LLM time: {combined_time:.2f} seconds")
            
            print()  # Add spacing
        
        total_end = time.time()
        total_duration = total_end - total_start
        
        # Print summary
        self._print_summary(total_duration)
    
    def _print_summary(self, total_duration: float):
        """Print test summary statistics."""
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in self.test_results if r["success"]]
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        print(f"Total tests run: {len(self.test_results)}")
        print(f"Successful: {len(successful_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success rate: {len(successful_tests)/len(self.test_results)*100:.1f}%")
        print(f"Total test time: {total_duration:.2f} seconds")
        
        if successful_tests:
            durations = [r["duration"] for r in successful_tests]
            print(f"\nResponse Time Statistics:")
            print(f"  Average: {sum(durations)/len(durations):.2f}s")
            print(f"  Min: {min(durations):.2f}s")
            print(f"  Max: {max(durations):.2f}s")
            
            # Breakdown by test type
            intent_tests = [r for r in successful_tests if r["test_type"] == "analyze_command_intent"]
            plan_tests = [r for r in successful_tests if r["test_type"] == "create_execution_plan"]
            
            if intent_tests:
                intent_avg = sum(r["duration"] for r in intent_tests) / len(intent_tests)
                print(f"  Intent analysis avg: {intent_avg:.2f}s")
            
            if plan_tests:
                plan_avg = sum(r["duration"] for r in plan_tests) / len(plan_tests)
                print(f"  Execution planning avg: {plan_avg:.2f}s")
        
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test_type']} for '{test['command'][:30]}...': {test['error']}")
        
        print(f"\n🎯 CONCLUSION:")
        if successful_tests and sum(r["duration"] for r in successful_tests) / len(successful_tests) < 10:
            print("✅ LLM performance is GOOD - issue likely in our system complexity")
        elif successful_tests:
            print("⚠️  LLM responses are SLOW - this explains the hanging issue")
        else:
            print("❌ LLM calls are FAILING - connection or API issues")


async def main():
    """Main entry point."""
    try:
        tester = LLMPerformanceTester()
        await tester.run_comprehensive_test()
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("LLM Performance Tester - Gemini 2.5 Flash")
    print("Tests raw LLM response times with actual system prompts")
    print()
    
    asyncio.run(main())