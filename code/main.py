from pathlib import Path
import pandas as pd

from data_loader import DataLoader
from context_builder import ContextBuilder
from multimodal import MultimodalProcessor
from decision_engine import DecisionEngine


def main():

    print("=" * 70)
    print("HACKERRANK ORCHESTRATE")
    print("SAMPLE VALIDATION")
    print("=" * 70)

    # Load all dataset files
    data = DataLoader()

    context_builder = ContextBuilder(data)

    dataset_path = (
        Path(__file__).resolve().parent.parent / "dataset"
    )

    multimodal_processor = MultimodalProcessor(
        dataset_path
    )

    decision_engine = DecisionEngine()

    # Use solved sample messages
    sample_df = data.sample_messages

    total = len(sample_df)
    action_correct = 0
    type_correct = 0
    both_correct = 0

    print(
        f"\nValidating {total} sample messages...\n"
    )

    results = []

    for _, row in sample_df.iterrows():

        message = row.to_dict()

        message_id = message["message_id"]

        # Save expected values before processing
        expected_action = str(
            message.get("action", "")
        ).strip().lower()

        expected_type = str(
            message.get("message_type", "")
        ).strip().lower()

        # -----------------------------------------
        # Process image / voice media
        # -----------------------------------------

        media_result = (
            multimodal_processor.process_message(
                message
            )
        )

        extracted_text = (
            media_result.get(
                "extracted_text",
                ""
            )
        )

        # -----------------------------------------
        # Combine message text and media text
        # -----------------------------------------

        original_text = str(
            message.get(
                "message_text",
                ""
            ) or ""
        ).strip()

        if extracted_text:

            if original_text:
                combined_text = (
                    original_text
                    + " "
                    + extracted_text
                )
            else:
                combined_text = extracted_text

        else:
            combined_text = original_text

        enriched_message = message.copy()

        enriched_message["message_text"] = (
            combined_text
        )

        # -----------------------------------------
        # Build context
        # -----------------------------------------

        context = (
            context_builder.build_context(
                enriched_message
            )
        )

        # -----------------------------------------
        # Get prediction
        # -----------------------------------------

        prediction = (
            decision_engine.decide(
                enriched_message,
                context
            )
        )

        predicted_action = prediction["action"]
        predicted_type = prediction["message_type"]

        # -----------------------------------------
        # Compare results
        # -----------------------------------------

        action_match = (
            predicted_action == expected_action
        )

        type_match = (
            predicted_type == expected_type
        )

        both_match = (
            action_match
            and type_match
        )

        if action_match:
            action_correct += 1

        if type_match:
            type_correct += 1

        if both_match:
            both_correct += 1

        status = (
            "CORRECT"
            if both_match
            else "WRONG"
        )

        print("-" * 70)

        print(
            f"{message_id} -> {status}"
        )

        print(
            f"Text: {combined_text[:150]}"
        )

        print(
            f"Expected Action : {expected_action}"
        )

        print(
            f"Predicted Action: {predicted_action}"
        )

        print(
            f"Expected Type   : {expected_type}"
        )

        print(
            f"Predicted Type  : {predicted_type}"
        )

        if not both_match:

            print(
                f"Debug Scores   : "
                f"{prediction.get('debug_scores')}"
            )

        results.append(
            {
                "message_id": message_id,

                "expected_action":
                    expected_action,

                "predicted_action":
                    predicted_action,

                "expected_type":
                    expected_type,

                "predicted_type":
                    predicted_type,

                "action_match":
                    action_match,

                "type_match":
                    type_match,

                "both_match":
                    both_match,
            }
        )

    # -----------------------------------------
    # Final summary
    # -----------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    print(
        f"Total Samples : {total}"
    )

    print(
        f"Action Correct: "
        f"{action_correct}/{total} "
        f"({action_correct / total * 100:.2f}%)"
    )

    print(
        f"Type Correct  : "
        f"{type_correct}/{total} "
        f"({type_correct / total * 100:.2f}%)"
    )

    print(
        f"Both Correct  : "
        f"{both_correct}/{total} "
        f"({both_correct / total * 100:.2f}%)"
    )

    # Save detailed validation results
    results_df = pd.DataFrame(results)

    validation_path = (
        dataset_path / "sample_validation.csv"
    )

    results_df.to_csv(
        validation_path,
        index=False
    )

    print(
        f"\nDetailed results saved to:"
    )

    print(
        validation_path
    )

    print("=" * 70)


if __name__ == "__main__":
    main()