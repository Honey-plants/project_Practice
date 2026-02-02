from AI.review.app.domain.schemas import PipelineContext
from AI.review.app.pipeline.step_5_final.step_5_create_JSON import run_build_final_response

def main():
    # 1) ctx 만들기
    ctx = PipelineContext(mode="debug")

    # 2) 필요한 값만 채우기 (build_final_response가 참조하는 필드들)
    ctx.store.store_name = "육전식당 2호점"
    ctx.store.address = "서울특별시 동대문구 한빛로 6"
    ctx.store.city = "서울특별시"
    ctx.store.coords = {"x": "1270000000", "y": "370000000"}  # 네 스키마에 맞게 dict/객체 형태 조정
    ctx.extracted.phone = "0222536373"
    ctx.extracted.menu_ko = ["통생삼겹살", "볶음밥"]

    # 3) 실행
    ctx = run_build_final_response(ctx)

    # 4) 결과 확인
    print("final =", ctx.final.model_dump() if hasattr(ctx.final, "model_dump") else ctx.final.dict())

if __name__ == "__main__":
    main()
