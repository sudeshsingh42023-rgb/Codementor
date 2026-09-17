"""
problems.py — the problem bank.

Each problem defines:
  - a function signature the student must implement
  - test cases (input args -> expected output)
  - a "reference" ideal time complexity, used to flag inefficient-but-correct solutions
  - a ladder of progressively stronger hints (used when the student is stuck or wrong)

Add a new problem by appending to PROBLEMS with the same shape.
"""

PROBLEMS = {
    "two_sum": {
        "id": "two_sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "prompt": (
            "Given a list of integers `nums` and an integer `target`, return the indices "
            "of the two numbers that add up to target. Assume exactly one solution exists, "
            "and you may not use the same element twice.\n\n"
            "Write a function: def two_sum(nums: list[int], target: int) -> list[int]"
        ),
        "function_name": "two_sum",
        "test_cases": [
            {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"args": [[3, 2, 4], 6], "expected": [1, 2]},
            {"args": [[3, 3], 6], "expected": [0, 1]},
            {"args": [[1, 5, 9, 11], 20], "expected": [2, 3]},
        ],
        "ideal_complexity": "O(n)",
        "hints": [
            "Think about what information you'd need to remember as you scan the list once.",
            "A hash map from value -> index lets you check 'have I seen target - current_value before?' in O(1).",
            "For each number x at index i, check if (target - x) is already a key in your map. If yes, return [map[target-x], i]. If no, store x -> i and keep going.",
        ],
    },
    "valid_parentheses": {
        "id": "valid_parentheses",
        "title": "Valid Parentheses",
        "difficulty": "easy",
        "prompt": (
            "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', "
            "determine if the input string is valid: every open bracket must be closed by the "
            "same type of bracket, in the correct order.\n\n"
            "Write a function: def valid_parentheses(s: str) -> bool"
        ),
        "function_name": "valid_parentheses",
        "test_cases": [
            {"args": ["()"], "expected": True},
            {"args": ["()[]{}"], "expected": True},
            {"args": ["(]"], "expected": False},
            {"args": ["([)]"], "expected": False},
            {"args": ["{[]}"], "expected": True},
            {"args": [""], "expected": True},
        ],
        "ideal_complexity": "O(n)",
        "hints": [
            "You need to match the most recently opened bracket first — what data structure gives you 'last in, first out' access?",
            "Push opening brackets onto a stack. When you see a closing bracket, it must match the top of the stack.",
            "If the stack is empty when you see a closing bracket, or the top doesn't match, return False immediately. At the end, the stack must be empty.",
        ],
    },
    "max_subarray": {
        "id": "max_subarray",
        "title": "Maximum Subarray",
        "difficulty": "medium",
        "prompt": (
            "Given an integer array `nums`, find the contiguous subarray (containing at least "
            "one number) which has the largest sum, and return that sum.\n\n"
            "Write a function: def max_subarray(nums: list[int]) -> int"
        ),
        "function_name": "max_subarray",
        "test_cases": [
            {"args": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
            {"args": [[1]], "expected": 1},
            {"args": [[5, 4, -1, 7, 8]], "expected": 23},
            {"args": [[-1, -2, -3]], "expected": -1},
        ],
        "ideal_complexity": "O(n)",
        "hints": [
            "A brute-force check of every subarray is O(n²) or worse. Can you track a running sum as you go?",
            "This is Kadane's Algorithm: at each index, decide whether to extend the previous subarray or start a new one at the current element.",
            "current = max(nums[i], current + nums[i]); best = max(best, current). Return best after scanning once.",
        ],
    },
}


def get_problem(problem_id: str):
    return PROBLEMS.get(problem_id)


def list_problems():
    return [
        {"id": p["id"], "title": p["title"], "difficulty": p["difficulty"], "prompt": p["prompt"]}
        for p in PROBLEMS.values()
    ]
