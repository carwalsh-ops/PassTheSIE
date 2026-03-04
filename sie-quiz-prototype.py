# SIE Exam Prep - Prototype Quiz Engine

questions = [
    {
        "id": 1,
        "category": "Securities Products",
        "question": "A customer buys 100 shares of ABC stock at $50 per share and writes a covered call with a strike price of $55. If the stock price rises to $60 at expiration, what is the maximum profit?",
        "options": ["$500", "$550", "$1,000", "$600"],
        "correct": 1,
        "explanation": "Covered call max profit = (Strike - Stock Price) + (Stock Price - Premium). The stock is called away at $55, so profit = ($55-$50) x 100 = $500, plus premium received."
    },
    {
        "id": 2,
        "category": "Economics",
        "question": "If the Federal Reserve increases the discount rate, what is the most likely immediate effect on the economy?",
        "options": ["Increased inflation", "Decreased borrowing", "Higher unemployment", "Lower GDP growth"],
        "correct": 1,
        "explanation": "Higher discount rate = higher borrowing costs = less borrowing = less economic activity."
    },
    {
        "id": 3,
        "category": "Client Accounts",
        "question": "Which account type allows for the highest contribution limits?",
        "options": ["Traditional IRA", "Roth IRA", "401(k)", "HSA"],
        "correct": 2,
        "explanation": "401(k) limits are highest ($23,000 in 2024), much higher than IRA limits."
    },
    {
        "id": 4,
        "category": "Ethics",
        "question": "A broker recommends a security that is suitable but also pays a higher commission than alternative products. What must the broker disclose?",
        "options": ["Nothing", "The conflict of interest", "Only to the compliance department", "Only at account opening"],
        "correct": 1,
        "explanation": "Brokers must disclose material conflicts of interest that could affect their recommendations."
    },
    {
        "id": 5,
        "category": "Regulation",
        "question": "What is the primary purpose of FINRA's Rule 2111 (Suitability)?",
        "options": ["Prevent fraud", "Ensure recommendations are suitable", "Protect customer assets", "Enforce licensing requirements"],
        "correct": 1,
        "explanation": "Rule 2111 requires brokers to obtain reasonable grounds for believing recommendations are suitable."
    }
]

# Game state
player = {
    "xp": 0,
    "level": 1,
    "streak": 0,
    "correct": 0,
    "total": 0
}

def get_xp_for_answer(correct, streak):
    base = 50 if correct else 10
    bonus = streak * 5 if correct else 0
    return base + bonus

def check_answer(q, answer_idx):
    is_correct = answer_idx == q["correct"]
    
    print("\n" + "="*50)
    if is_correct:
        print("✅ CORRECT!")
        print(f"Explanation: {q['explanation']}")
    else:
        print("❌ INCORRECT")
        print(f"Correct answer: {q['options'][q['correct']]}")
        print(f"Explanation: {q['explanation']}")
    print("="*50)
    
    return is_correct

def main():
    import random
    
    print("📚 SIE EXAM PREP")
    print("="*40)
    print(f"Level {player['level']} | XP: {player['xp']} | Streak: {player['streak']}")
    print("="*40 + "\n")
    
    # Shuffle questions
    quiz_questions = random.sample(questions, len(questions))
    
    for i, q in enumerate(quiz_questions, 1):
        print(f"Question {i}/{len(quiz_questions)}")
        print(f"Category: {q['category']}")
        print(f"\n{q['question']}\n")
        
        for j, opt in enumerate(q["options"]):
            print(f"  {j+1}. {opt}")
        
        try:
            answer = int(input("\nYour answer (1-4): ")) - 1
        except ValueError:
            answer = -1
        
        if 0 <= answer < 4:
            is_correct = check_answer(q, answer)
            
            if is_correct:
                player["correct"] += 1
                player["streak"] += 1
            else:
                player["streak"] = 0
            
            xp = get_xp_for_answer(is_correct, player["streak"])
            player["xp"] += xp
            player["total"] += 1
            
            # Level up check
            xp_needed = player["level"] * 200
            if player["xp"] >= xp_needed:
                player["level"] += 1
                print(f"\n🎉 LEVEL UP! You're now level {player['level']}!")
            
            print(f"\n+{xp} XP | Total: {player['xp']}/{xp_needed}")
        else:
            print("Invalid answer, skipping...")
    
    # End game
    print("\n" + "="*50)
    print("📊 QUIZ COMPLETE!")
    print(f"Score: {player['correct']}/{player['total']} ({player['correct']*100//player['total']}%)")
    print(f"Final XP: {player['xp']} | Level: {player['level']}")
    print("="*50)

if __name__ == "__main__":
    main()
