import { useState } from "react";
import AiModal from "../../components/common/AIModal";
import '../../styles/Community.css';

export default function Community () {

    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="container">
            <h1>Community</h1>

            <div className="create_img">
                <button onClick={() => setIsOpen(true)}>
                이미지 생성하기
                </button>
            </div>

            {/* 모달 */}
            <AiModal isOpen={isOpen} onClose={() => setIsOpen(false)}>
                <h2>AI 이미지 생성</h2>
                <p>리뷰 3개 이상 작성 시 이미지를 생성할 수 있습니다.</p>

                <button onClick={() => setIsOpen(false)}>
                생성하기
                </button>
            </AiModal>

            <div className='notice'>
                <div className='text'>
                    <p>현재 0개의 리뷰를 쓰셨습니다.</p>
                    <span>리뷰를 3개 이상 쓰시면 AI로 나만의 이미지를 만들 수 있습니다.</span>
                </div>
                <button>리뷰 남기러 가기</button>
            </div>
            <div className='ctn_box'>
                <div className='ai_img'>ai image</div>
                <div className="row">
                    <div className="left">
                        <div className='icon'>
                            <div className='profile'>icon</div>
                            <div className='nickname'>nickname</div>
                        </div>
                    </div>

                    <div className="right">
                        <div className="right-top">
                            <button className="toggle toggle-text" aria-pressed="false">
                                <span className="toggle-option left">Open</span>
                                <span className="toggle-track">
                                    <span className="toggle-thumb"></span>
                                </span>
                                <span className="toggle-option right">Private</span>
                            </button>
                        </div>
                        <div className="right-bottom">
                            <div className='like'>
                                <span className='icon'>♥</span>
                                <span className='text'>Like</span>
                                <span className='num'>32</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className='row comment'>
                    <div className='left'>
                        That's a really funny image!
                    </div>
                    <div className='right icon'>   
                        <div className='right-top profile'>icon</div>
                        <div className='right-bottom nickname'>nickname</div>
                    </div>
                </div>
                
                <div className='row comment'>
                    <div className='left'>
                        That's a really funny image!
                    </div>
                    <div className='right icon'>   
                        <div className='right-top profile'>icon</div>
                        <div className='right-bottom nickname'>nickname</div>
                    </div>
                </div>
            </div>


            
            <div className='ctn_box'>
                <div className='ai_img'>ai image</div>
                <div className="row">
                    <div className="left">
                        <div className='icon'>
                            <div className='profile'>icon</div>
                            <div className='nickname'>nickname</div>
                        </div>
                    </div>

                    <div className="right">
                        <div className="right-top">
                            <button className="toggle toggle-text" aria-pressed="false">
                                <span className="toggle-option left">Open</span>
                                <span className="toggle-track">
                                    <span className="toggle-thumb"></span>
                                </span>
                                <span className="toggle-option right">Private</span>
                            </button>
                        </div>
                        <div className="right-bottom">
                            <div className='like'>
                                <span className='icon'>♥</span>
                                <span className='text'>Like</span>
                                <span className='num'>32</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className='row comment'>
                    <div className='left'>
                        That's a really funny image!
                    </div>
                    <div className='right icon'>   
                        <div className='right-top profile'>icon</div>
                        <div className='right-bottom nickname'>nickname</div>
                    </div>
                </div>
                
                <div className='row comment'>
                    <div className='left'>
                        That's a really funny image!
                    </div>
                    <div className='right icon'>   
                        <div className='right-top profile'>icon</div>
                        <div className='right-bottom nickname'>nickname</div>
                    </div>
                </div>
            </div>
        </div>
    )
};