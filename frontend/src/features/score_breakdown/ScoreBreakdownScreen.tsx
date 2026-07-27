"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/src/lib/apiClient";
import { ScoreBreakdownData } from "./types";
import styles from "./ScoreBreakdownScreen.module.css";

function formatEquipment(list: string[] | undefined, score: number) {
    if (list && list.length > 0) {
        return `装備：${list.join(" ・ ")} → ${score}`;
    }
    return "装備：なし → 0";
}

export default function ScoreBreakdownScreen() {
    const router = useRouter();
    const [breakdown, setBreakdown] = useState<ScoreBreakdownData | null>(null);

    useEffect(() => {
        apiGet("/api/score_breakdown/")
            .then((res: { breakdown: ScoreBreakdownData }) => {
                setBreakdown(res.breakdown);
            })
            .catch(() => {
                // HTML版同様、内訳がなければゲームオーバーへ
                router.replace("/game/gameover");
            });
    }, [router]);

    return (
        <div className={styles.page}>
            <div className={styles.breakdownContainer}>
                <h1 className={styles.breakdownTitle}>内訳</h1>
                <div className={styles.breakdownFrame}>
                    {breakdown && (
                        <>
                            <div className={styles.breakdownItem}>
                                HP : {breakdown.hp} → {breakdown.hp_score}
                            </div>
                            <div className={styles.breakdownItem}>
                                ATK : {breakdown.atk} → {breakdown.atk_score}
                            </div>
                            <div className={styles.breakdownItem}>
                                DEF : {breakdown.defense} → {breakdown.def_score}
                            </div>
                            <div className={styles.breakdownItem}>
                                SPD : {breakdown.spd} → {breakdown.spd_score}
                            </div>
                            <div className={styles.breakdownItem}>
                                SP : {breakdown.mp} → {breakdown.mp_score}
                            </div>
                            <div className={styles.breakdownEquipment}>
                                {formatEquipment(breakdown.equipment_list, breakdown.equipment_score)}
                            </div>
                            <div className={styles.breakdownItem}>
                                倒した敵の数 : {breakdown.defeats} → {breakdown.defeat_score}
                            </div>
                            <div className={styles.breakdownItem}>
                                倒した強敵の数 : {breakdown.strong_defeats} → {breakdown.strong_defeat_score}
                            </div>
                            <div className={styles.breakdownItem}>
                                プレイヤーレベル : {breakdown.level} → {breakdown.level_score}
                            </div>
                            <div className={styles.totalScore}>
                                合計スコア：{breakdown.total_score}
                            </div>
                        </>
                    )}
                </div>
                <button
                    className={styles.backButton}
                    type="button"
                    onClick={() => router.push("/game/gameover")}
                >
                    戻る
                </button>
            </div>
        </div>
    );
}
