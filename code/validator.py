import os
import sys

import pandas as pd

from data_loader import DataLoader
from context_builder import ContextBuilder
from decision_engine import DecisionEngine
from multimodal import MultimodalProcessor


def clean_value(value):
    """
    Convert NaN and missing values to safe Python values.
    """

    if pd.isna(value):
        return None

    return value


def combine_message_and_media(message, multimodal_result):
    """
    Combine original message text with text extracted
    from images or voice notes.
    """

    message = message.copy()

    original_text = message.get(
        "message_text",
        ""
    )

    if pd.isna(original_text):
        original_text = ""

    original_text = str(original_text).strip()

    extracted_text = multimodal_result.get(
        "extracted_text",
        ""
    )

    if extracted_text is None:
        extracted_text = ""

    extracted_text = str(
        extracted_text
    ).strip()

    if original_text and extracted_text:
        combined_text = (
            original_text
            + " "
            + extracted_text
        )

    elif extracted_text:
        combined_text = extracted_text

    else:
        combined_text = original_text

    message["message_text"] = combined_text

    return message


def main():

    print("=" * 70)
    print("HACKERRANK ORCHESTRATE")
    print("SAMPLE VALIDATION")
    print("=" * 70)

    data = DataLoader()

    context_builder = ContextBuilder(
        data
    )

    decision_engine = DecisionEngine()

    multimodal_processor = MultimodalProcessor()

    sample_df = data.sample_messages

    validation_path = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ),
        "dataset",
        "sample_validation.csv"
    )

    if not os.path.exists(
        validation_path
    ):
        print(
            "\nERROR: sample_validation.csv "
            "was not found."
        )

        print(
            "\nExpected location:"
        )

        print(
            validation_path
        )

        return

    validation_df = pd.read_csv(
        validation_path
    )

    if sample_df is None or sample_df.empty:

        print(
            "\nERROR: sample_messages.csv "
            "could not be loaded."
        )

        return

    if validation_df.empty:

        print(
            "\nERROR: sample_validation.csv "
            "is empty."
        )

        return

    print(
        f"\nValidating "
        f"{len(validation_df)} sample messages..."
    )

    results = []

    action_correct = 0
    type_correct = 0
    both_correct = 0

    for _, validation_row in (
        validation_df.iterrows()
    ):

        message_id = str(
            validation_row[
                "message_id"
            ]
        )

        expected_action = str(
            validation_row[
                "expected_action"
            ]
        ).strip().lower()

        expected_type = str(
            validation_row[
                "expected_type"
            ]
        ).strip().lower()

        matching_rows = sample_df[
            sample_df["message_id"]
            .astype(str)
            == message_id
        ]

        if matching_rows.empty:

            print(
                "\nWARNING: "
                f"{message_id} not found "
                "in sample_messages.csv"
            )

            continue

        message = (
            matching_rows
            .iloc[0]
            .to_dict()
        )

        # -----------------------------------------------------
        # Clean NaN values
        # -----------------------------------------------------

        message = {
            key: clean_value(value)
            for key, value
            in message.items()
        }

        # -----------------------------------------------------
        # Process image / voice media
        # -----------------------------------------------------

        multimodal_result = (
            multimodal_processor
            .process_message(
                message
            )
        )

        message = (
            combine_message_and_media(
                message,
                multimodal_result
            )
        )

        # -----------------------------------------------------
        # Build complete context
        # -----------------------------------------------------

        context = (
            context_builder
            .build_context(
                message
            )
        )

        # -----------------------------------------------------
        # Get prediction
        # -----------------------------------------------------

        prediction = (
            decision_engine
            .decide(
                message,
                context
            )
        )

        predicted_action = str(
            prediction[
                "action"
            ]
        ).strip().lower()

        predicted_type = str(
            prediction[
                "message_type"
            ]
        ).strip().lower()

        is_action_correct = (
            predicted_action
            == expected_action
        )

        is_type_correct = (
            predicted_type
            == expected_type
        )

        is_both_correct = (
            is_action_correct
            and is_type_correct
        )

        if is_action_correct:
            action_correct += 1

        if is_type_correct:
            type_correct += 1

        if is_both_correct:
            both_correct += 1

        # -----------------------------------------------------
        # Print result
        # -----------------------------------------------------

        print(
            "\n"
            + "-" * 70
        )

        if is_both_correct:
            status = "CORRECT"
        else:
            status = "WRONG"

        print(
            f"{message_id} -> {status}"
        )

        print(
            f"Text: "
            f"{message.get('message_text', '')}"
        )

        print(
            f"Expected Action : "
            f"{expected_action}"
        )

        print(
            f"Predicted Action: "
            f"{predicted_action}"
        )

        print(
            f"Expected Type   : "
            f"{expected_type}"
        )

        print(
            f"Predicted Type  : "
            f"{predicted_type}"
        )

        if not is_both_correct:

            print(
                f"Debug Scores   : "
                f"{prediction.get('debug_scores')}"
            )

        results.append(
            {
                "message_id":
                    message_id,

                "expected_action":
                    expected_action,

                "predicted_action":
                    predicted_action,

                "expected_type":
                    expected_type,

                "predicted_type":
                    predicted_type,

                "action_match":
                    is_action_correct,

                "type_match":
                    is_type_correct,

                "both_match":
                    is_both_correct,
            }
        )

    # ---------------------------------------------------------
    # Save detailed results
    # ---------------------------------------------------------

    results_df = pd.DataFrame(
        results
    )

    output_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "sample_validation_results.csv"
    )

    results_df.to_csv(
        output_path,
        index=False
    )

    total = len(results)

    if total == 0:

        print(
            "\nNo messages were validated."
        )

        return

    action_percentage = (
        action_correct
        / total
        * 100
    )

    type_percentage = (
        type_correct
        / total
        * 100
    )

    both_percentage = (
        both_correct
        / total
        * 100
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "VALIDATION RESULTS"
    )

    print(
        "=" * 70
    )

    print(
        f"Total Samples : {total}"
    )

    print(
        f"Action Correct: "
        f"{action_correct}/{total} "
        f"({action_percentage:.2f}%)"
    )

    print(
        f"Type Correct  : "
        f"{type_correct}/{total} "
        f"({type_percentage:.2f}%)"
    )

    print(
        f"Both Correct  : "
        f"{both_correct}/{total} "
        f"({both_percentage:.2f}%)"
    )

    print(
        "\nDetailed results saved to:"
    )

    print(
        output_path
    )


if __name__ == "__main__":
    main()