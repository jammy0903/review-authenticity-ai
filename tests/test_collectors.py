import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.collectors.base import RawReviewRecord, records_to_dataframe
from src.collectors.coupang import parse_coupang_reviews
from src.collectors.coupang_eats import parse_coupang_eats_reviews
from src.collectors.kakaomap import parse_kakaomap_reviews
from src.collect_reviews import load_html_file_list, load_url_list


class CollectorTests(unittest.TestCase):
    def test_records_to_dataframe_deduplicates_platform_review_id(self):
        records = [
            RawReviewRecord(
                review_id="cp_1",
                platform="coupang",
                store_or_product_name="상품",
                review_text_raw="첫 리뷰",
            ),
            RawReviewRecord(
                review_id="cp_1",
                platform="coupang",
                store_or_product_name="상품",
                review_text_raw="중복 리뷰",
            ),
        ]

        dataframe = records_to_dataframe(records)

        self.assertEqual(len(dataframe), 1)
        self.assertEqual(dataframe[0]["review_text_raw"], "첫 리뷰")

    def test_parse_coupang_reviews_from_html_nodes(self):
        html = """
        <html>
          <head><meta property="og:title" content="테스트 상품" /></head>
          <body>
            <article class="sdp-review__article__list" data-review-id="101">
              <div class="js_reviewArticleRatingValue">5</div>
              <div class="sdp-review__article__list__review__content">배송이 빨랐고 포장도 깔끔했어요.</div>
            </article>
          </body>
        </html>
        """

        records = parse_coupang_reviews(html, source_url="https://www.coupang.com/vp/products/123")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].review_id, "101")
        self.assertEqual(records[0].platform, "coupang")
        self.assertEqual(records[0].store_or_product_name, "테스트 상품")
        self.assertEqual(records[0].review_text_raw, "배송이 빨랐고 포장도 깔끔했어요.")

    def test_parse_coupang_eats_reviews_from_json_script(self):
        html = """
        <html>
          <head><meta property="og:title" content="테스트 가게" /></head>
          <body>
            <script>
              window.__APOLLO_STATE__ = [{"id":"9001","reviewText":"양이 많고 배달이 빨랐어요.","rating":5,"imageUrls":["a.jpg"]}];
            </script>
          </body>
        </html>
        """

        records = parse_coupang_eats_reviews(html)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].review_id, "9001")
        self.assertEqual(records[0].platform, "coupang_eats")
        self.assertEqual(records[0].store_or_product_name, "테스트 가게")
        self.assertEqual(records[0].has_photo, 1)

    def test_parse_kakaomap_reviews_from_json_script(self):
        html = """
        <html>
          <head><meta property="og:title" content="테스트 식당" /></head>
          <body>
            <script>
              window.__PLACE_STATE__ = {
                "reviews": [
                  {"id":"km_1001","comment":"국물이 진하고 김치가 아삭해서 좋았어요.","point":4,"photoCount":1}
                ]
              };
            </script>
          </body>
        </html>
        """

        records = parse_kakaomap_reviews(html, source_url="https://place.map.kakao.com/123456789")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].review_id, "km_1001")
        self.assertEqual(records[0].platform, "kakaomap")
        self.assertEqual(records[0].store_or_product_name, "테스트 식당")
        self.assertEqual(records[0].has_photo, 1)
        self.assertIn("place_id=123456789", records[0].source_note)

    def test_load_url_list_skips_blank_lines_and_comments(self):
        with TemporaryDirectory() as temp_dir:
            url_file = Path(temp_dir) / "urls.txt"
            url_file.write_text(
                "# seed urls\n\nhttps://www.coupang.com/vp/products/1\nhttps://www.coupang.com/vp/products/2\n",
                encoding="utf-8",
            )

            urls = load_url_list(url_file)

        self.assertEqual(
            urls,
            [
                "https://www.coupang.com/vp/products/1",
                "https://www.coupang.com/vp/products/2",
            ],
        )

    def test_load_html_file_list_returns_sorted_html_files(self):
        with TemporaryDirectory() as temp_dir:
            html_dir = Path(temp_dir)
            (html_dir / "b.html").write_text("<html></html>", encoding="utf-8")
            (html_dir / "a.html").write_text("<html></html>", encoding="utf-8")
            (html_dir / "ignore.txt").write_text("x", encoding="utf-8")

            html_files = load_html_file_list(html_dir, "*.html")

        self.assertEqual([path.name for path in html_files], ["a.html", "b.html"])


if __name__ == "__main__":
    unittest.main()
