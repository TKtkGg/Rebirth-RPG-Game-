"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/src/lib/apiClient";
import { GameOverData } from "./types";
import styles from "./GameOverScreen.module.css";

export default function GameOverScreen() {
    const router = useRouter();
    const [data, setData] = useState<GameOverData | null>(null);
    const [displayScore, setDisplayScore] = useState(0);
    const [displayPoint, setDisplayPoint] = useState(0);

    useEffect(() => {
        apiGet("/api/gameover/").then((res: GameOverData) => {
            setData(res);
            // HTML版同様、Score は初期値を表示し、ポイントは 0 から開始
            setDisplayScore(res.score);
            setDisplayPoint(0);
        });
    }, []);

    useEffect(() => {
        if (!data) return;

        // gameover.js と同じロジック
        const startScore = data.score;
        const targetInitPoint = data.initial_point;
        const scoreStep = 31111 / 60; // 60fps相当
        const totalFrames = Math.ceil(startScore / scoreStep) || 0;

        let currentScore = startScore;
        let currentPoint = 0;
        let frame = 0;
        let rafId = 0;

        const animate = () => {
            if (currentScore > 0) {
                currentScore = Math.max(0, currentScore - scoreStep);
                setDisplayScore(Math.floor(currentScore));
            }
            // 初期ポイントはスコアが0になるまで均等に増やす
            if (totalFrames > 0 && frame < totalFrames) {
                currentPoint = Math.floor(targetInitPoint * (frame / totalFrames));
                setDisplayPoint(currentPoint);
            } else {
                currentPoint = targetInitPoint;
                setDisplayPoint(targetInitPoint);
            }
            frame++;
            if (currentScore > 0 || currentPoint < targetInitPoint) {
                rafId = window.requestAnimationFrame(animate);
            }
        };

        rafId = window.requestAnimationFrame(animate);
        return () => window.cancelAnimationFrame(rafId);
    }, [data]);

    return (
        <div className={styles.page}>
            <div className={styles.gameoverContainer}>
                <h1 className={styles.gameoverTitle}>GAME OVER</h1>
                <div className={styles.scoreInfo}>
                    <div>
                        <span className={styles.scoreLabel}>Score：</span>
                        <span>{displayScore}</span>
                    </div>
                    <div className={styles.scorePointRow}>
                        <span className={styles.scoreLabel}>スコアポイント：</span>
                        <span>{displayPoint}</span>
                    </div>
                </div>
            </div>
            <div className={styles.gameoverButtons}>
                <button
                    className={styles.gameoverBtn}
                    type="button"
                    onClick={() => router.push("/game/score_breakdown")}
                >
                    内訳を確認する
                </button>
                <div className={styles.gameoverActions}>
                    <button
                        className={styles.gameoverBtn}
                        type="button"
                        onClick={() => router.push("/auth/")}
                    >
                        タイトルに戻る
                    </button>
                    {data && !data.is_guest ? (
                        <button
                            className={styles.gameoverBtn}
                            type="button"
                            // Step4 で遷移実装
                        >
                            ポイント分けへ
                        </button>
                    ) : null}
                </div>
            </div>
        </div>
    );
}
