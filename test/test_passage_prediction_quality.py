import unittest

from routes.helpers import build_prediction_response


class PassagePredictionQualityTests(unittest.TestCase):
    def test_gibberish_passage_is_classified_easy(self):
        text = """qweqwewqeqweqw
ewqe
qwewqeqwe
qweqwewqEqwewq qwe qwe wqe wqeqweqw
qwewqe wqe wqe
qweqweqwewqeqwewqe qwewq
ewqe wqe qw ewqeqweqw
weqeqwe wqe wq ewq ewq ewq
qwewqe wq wqe wqewqeqw qwe wqewqewq ewqe
wqewqewqe qwe wqewq"""

        result = build_prediction_response(text)

        self.assertEqual(result["label"], "EASY")
        self.assertEqual(result["features"]["passage_length"], 33)
        self.assertEqual(result["features"]["type_token_ratio"], 0.576)

    def test_varied_science_passage_keeps_model_classification(self):
        text = (
            "Photosynthesis is the process by which green plants convert sunlight into chemical energy. "
            "Chlorophyll absorbs light, while roots draw water and minerals from the soil. "
            "The plant combines these materials with carbon dioxide to produce glucose and release oxygen "
            "into the atmosphere."
        )

        result = build_prediction_response(text)

        self.assertEqual(result["label"], "MODERATE")

    def test_repeated_passage_is_classified_easy(self):
        text = "The dog is jumping in the backyard.\n" * 10

        result = build_prediction_response(text)

        self.assertEqual(result["label"], "EASY")


if __name__ == "__main__":
    unittest.main()