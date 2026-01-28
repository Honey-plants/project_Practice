C:\Users\201\Desktop\final_project\ai\review> 

python -c "from pathlib import Path; from receipt_service import process_receipt_ocr; preprocess_image(Path('tmp_receipt/receipt_5.jpg').read_bytes())"

-receipt -> OCR_raw.json
python -c "from pathlib import Path; from review.receipt_service import process_receipt_ocr; process_receipt_ocr(Path('review/tmp_receipt/receipt_7.jpg').read_bytes())"

step 1 test:
final step1_rectify_cli.py command: (input image path, output folder path)
python -m AI.review.app.pipeline.step_1_rectify.step_1_rectify_cli .\AI\review\app\pipeline\step_1_rectify\img_1.png --out .\AI\review\app\pipeline\debug_out

step 2 test:
python -m AI.review.app.pipeline.step_2_ocr.step_2_ocr_cli .\AI\review\app\pipeline\debug_out\20_post_for_ocr.jpg --out .\AI\review\app\pipeline\debug_ocr --debug



step 3: 
normalize_cli 돌리기 using json as input(state json file path)
python -m AI.review.app.pipeline.step_3_normalize.step_3_normalize_cli AI/review/app/pipeline/debug_ocr/ocr_result.json --out .\AI\review\app\pipeline\debug_norm --y-threshold 15 

step 4:
python -m AI.review.app.pipeline.step_4_enrich_data.step_4_enrich_cli .\AI\review\app\pipeline\debug\step3
_normalize_result.json --out .\debug\step4 --debug --naver-id NAVER_CLIENT_ID --naver-secret NAVER_API --gemini-key GOOGLE_API
python -m AI.review.app.pipeline.step_4_enrich_data.step_4_enrich_cli .\AI\review\app\pipeline\debug_norm\step3_normalize_result.json --out .\AI\review\app\pipeline\debug_enrich --debug ----naver-id NAVER_CLIENT_ID --naver-secret NAVER_API --gemini-key GOOGLE_API
  --out .\debug\step4 --debug










