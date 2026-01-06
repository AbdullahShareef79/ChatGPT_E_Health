"""
Test GPT responses to understand truncation behavior and response formats
"""
import os
import openai
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print("ERROR: No OpenAI API key found!")
    exit(1)

openai.api_key = OPENAI_API_KEY

def test_phq9_parsing():
    """Test the parse_with_gpt function behavior"""
    print("\n" + "="*80)
    print("TEST 1: PHQ-9 Response Parsing (max_tokens=10)")
    print("="*80)
    
    test_responses = [
        "I feel that way almost every day",
        "sometimes",
        "not really",
        "all the time",
        "I don't know, maybe a few times last week"
    ]
    
    prompt = "Question: Over the last 2 weeks, how often have you felt down, depressed, or hopeless?\n0=Not at all, 1=Several days, 2=More than half, 3=Nearly every day\nRespond: NUMBER|PHRASE"
    
    for user_response in test_responses:
        print(f"\n📝 User said: \"{user_response}\"")
        print("-" * 80)
        
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_response}
                ],
                temperature=0,
                max_tokens=10
            )
            
            result = resp.choices[0].message.content.strip()
            finish_reason = resp.choices[0].finish_reason
            tokens_used = resp.usage.total_tokens if hasattr(resp, 'usage') else None
            
            print(f"✅ GPT Response: \"{result}\"")
            print(f"   Finish Reason: {finish_reason}")
            print(f"   Tokens Used: {tokens_used}")
            
            # Check if truncated
            if finish_reason == "length":
                print("   ⚠️  WARNING: Response was TRUNCATED!")
            
            # Try to parse like the real code does
            parts = result.split('|')
            if len(parts) >= 2:
                score = int(parts[0].strip())
                confirm = parts[1].strip()
                print(f"   Parsed Score: {score}")
                print(f"   Confirmation: \"{confirm}\"")
            else:
                print(f"   ❌ Failed to parse - expected NUMBER|PHRASE format")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_confirmation_check():
    """Test the check_confirmation_with_gpt function"""
    print("\n" + "="*80)
    print("TEST 2: Confirmation Checking (max_tokens=3)")
    print("="*80)
    
    test_responses = [
        "yes",
        "yeah that's right",
        "no",
        "I'm not sure",
        "correct",
        "actually no",
        "yep"
    ]
    
    for user_response in test_responses:
        print(f"\n📝 User said: \"{user_response}\"")
        print("-" * 80)
        
        try:
            prompt = "Reply YES if confirming, NO if not."
            user_msg = f"Is '{user_response}' a confirmation?"
            
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0,
                max_tokens=3
            )
            
            result = resp.choices[0].message.content.strip().upper()
            finish_reason = resp.choices[0].finish_reason
            tokens_used = resp.usage.total_tokens if hasattr(resp, 'usage') else None
            
            print(f"✅ GPT Response: \"{result}\"")
            print(f"   Finish Reason: {finish_reason}")
            print(f"   Tokens Used: {tokens_used}")
            print(f"   Interpreted as: {'CONFIRMED' if 'YES' in result else 'NOT CONFIRMED'}")
            
            if finish_reason == "length":
                print("   ⚠️  WARNING: Response was TRUNCATED!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_fallback_parsing():
    """Test the call_gpt_fallback function"""
    print("\n" + "="*80)
    print("TEST 3: Fallback Parsing (max_tokens=5)")
    print("="*80)
    
    test_responses = [
        "I feel terrible all the time",
        "rarely",
        "sometimes I guess",
        "never"
    ]
    
    question = "Over the last 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?"
    
    for user_response in test_responses:
        print(f"\n📝 User said: \"{user_response}\"")
        print("-" * 80)
        
        try:
            prompt = f"""The user is answering PHQ-9: {question}
User said: "{user_response}"

Options: Not at all (0), Several days (1), More than half (2), Nearly every day (3)
Respond with ONLY the number 0, 1, 2, or 3."""

            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0,
                max_tokens=5
            )
            
            result = resp.choices[0].message.content.strip()
            finish_reason = resp.choices[0].finish_reason
            tokens_used = resp.usage.total_tokens if hasattr(resp, 'usage') else None
            
            print(f"✅ GPT Response: \"{result}\"")
            print(f"   Finish Reason: {finish_reason}")
            print(f"   Tokens Used: {tokens_used}")
            
            # Extract score like the real code does
            score = int(result[0]) if result and result[0] in "0123" else 1
            print(f"   Extracted Score: {score}")
            
            if finish_reason == "length":
                print("   ⚠️  WARNING: Response was TRUNCATED!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def test_with_increased_tokens():
    """Test what happens with more tokens to see full responses"""
    print("\n" + "="*80)
    print("TEST 4: Same test with max_tokens=50 (to see what GPT wanted to say)")
    print("="*80)
    
    user_response = "I feel that way almost every day"
    prompt = "Question: Over the last 2 weeks, how often have you felt down, depressed, or hopeless?\n0=Not at all, 1=Several days, 2=More than half, 3=Nearly every day\nRespond: NUMBER|PHRASE"
    
    print(f"\n📝 User said: \"{user_response}\"")
    print("-" * 80)
    
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_response}
            ],
            temperature=0,
            max_tokens=50
        )
        
        result = resp.choices[0].message.content.strip()
        finish_reason = resp.choices[0].finish_reason
        tokens_used = resp.usage.total_tokens if hasattr(resp, 'usage') else None
        
        print(f"✅ GPT Full Response: \"{result}\"")
        print(f"   Finish Reason: {finish_reason}")
        print(f"   Tokens Used: {tokens_used}")
        print(f"   Response Length: {len(result)} characters")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    print("\n🧪 Testing GPT Response Behavior in PHQ-9 Experiment")
    print("=" * 80)
    print("This will show you exactly what GPT returns and if truncation occurs")
    print("=" * 80)
    
    test_phq9_parsing()
    test_confirmation_check()
    test_fallback_parsing()
    test_with_increased_tokens()
    
    print("\n" + "="*80)
    print("✅ Testing Complete!")
    print("="*80)
    print("\nKEY FINDINGS TO TELL YOUR SUPERVISOR:")
    print("1. Check if any responses show 'finish_reason: length' (truncation)")
    print("2. Compare responses with max_tokens=10 vs max_tokens=50")
    print("3. Note how often parsing fails due to unexpected format")
    print("4. See if GPT follows the NUMBER|PHRASE instruction consistently")
