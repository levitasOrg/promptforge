import sys
from rich.console import Console
from promptforge.questions.models import ClarifyingQuestion, UserAnswer

_console = Console(stderr=True)

class Interviewer:
    def conduct(self, questions: list[ClarifyingQuestion], batch: bool = False) -> list[UserAnswer]:
        if not questions:
            return []
        answers: list[UserAnswer] = []
        if batch:
            # Print all questions first
            _console.print("\n[bold]Clarifying questions:[/bold]")
            for i, q in enumerate(questions, 1):
                _console.print(f"\n[{i}/{len(questions)}] {q.question_text}")
            _console.print()
            # Read all answers
            for i, q in enumerate(questions, 1):
                try:
                    text = input(f"Answer {i}: ").strip()
                except EOFError:
                    text = ""
                answers.append(UserAnswer(
                    question_id=q.question_id,
                    answer_text=text,
                    skipped=not bool(text),
                ))
        else:
            # Interactive: one at a time
            _console.print()
            for i, q in enumerate(questions, 1):
                _console.print(f"[bold][{i}/{len(questions)}][/bold] {q.question_text}")
                try:
                    text = input("> ").strip()
                except EOFError:
                    text = ""
                answers.append(UserAnswer(
                    question_id=q.question_id,
                    answer_text=text,
                    skipped=not bool(text),
                ))
                _console.print()
        return answers
