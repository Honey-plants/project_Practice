import { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import '../../styles/Community.css';
import CommunityList from "./CommunityList";

export default function Community () {

    const nav = useNavigate();

    return (
        <div className="container">
            <h1>Community</h1>

            {/* 이미지 생성 페이지로 이동 */}
            <div className="create_img">
                <button onClick={()=>nav('/community/new')}>
                    Generate Image
                </button>
            </div>

            <div className='notice'>
                <div className='text'>
                    <p>현재 0개의 리뷰를 쓰셨습니다.</p>
                    <span>리뷰를 3개 이상 쓰시면 AI로 나만의 이미지를 만들 수 있습니다.</span>
                </div>
                <button>리뷰 남기러 가기</button>
            </div>

            {/* Community.List 컴포넌트 불러오기 */}
            <CommunityList />
            
        </div>
    )
};