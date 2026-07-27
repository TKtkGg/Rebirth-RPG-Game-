"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/src/lib/apiClient";
import { GameOverData } from "./types";
import styles from "./GameOverScreen.module.css";

export default function GameOverScreen() {
    const router = useRouter();
    const [data, setData] = useState<GameOverData | null>(null);

    useEffect(() => {
        apiGet("/api/gameover/").then((res: GameOverData) => {
            setData(res);
        });
    }, []);

    // Step1: スコア数値のカウント演出は未実装（レイアウトのみ。値は HTML 初期表示と同じ 0）
    const displayScore = 0;
    const displayPoint = 0;

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
                    // Step3 で遷移実装
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
