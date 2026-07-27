"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/src/lib/apiClient";
import { ScorePointsData } from "./types";
import styles from "./ScorePointsScreen.module.css";

export default function ScorePointsScreen() {
    const router = useRouter();
    const [data, setData] = useState<ScorePointsData | null>(null);
    const [categoryKey, setCategoryKey] = useState("all");

    const load = useCallback((category: string) => {
        apiGet(`/api/score_points/?category=${encodeURIComponent(category)}`)
            .then((res: ScorePointsData) => {
                setData(res);
                setCategoryKey(res.category_key);
            })
            .catch(() => {
                // HTML版同様、未ログインは start へ
                router.replace("/game/start");
            });
    }, [router]);

    useEffect(() => {
        load("all");
    }, [load]);

    const handleCategory = (key: string) => {
        setCategoryKey(key);
        load(key);
    };

    const handleAllocate = (statKey: string) => {
        apiPost("/api/score_points/", {
            category: categoryKey,
            stat: statKey,
        }).then((res: ScorePointsData) => {
            setData(res);
            setCategoryKey(res.category_key);
        });
    };

    return (
        <div className={styles.page}>
            <div className={styles.scoreTitle}>スコアポイント振り分け</div>
            <div className={styles.scorePointsBoard}>
                <div className={styles.categoryList}>
                    {(data?.categories ?? []).map((category) => (
                        <div key={category.key} className={styles.categoryForm}>
                            <button
                                className={
                                    category.key === categoryKey
                                        ? `${styles.categoryItem} ${styles.categoryItemActive}`
                                        : styles.categoryItem
                                }
                                type="button"
                                onClick={() => handleCategory(category.key)}
                            >
                                {category.label}
                            </button>
                        </div>
                    ))}
                </div>
                <div className={styles.contentArea}>
                    <div className={styles.statsGrid}>
                        {(data?.stat_items ?? []).map((item) => (
                            <div key={item.key} className={styles.statCard}>
                                <div
                                    className={styles.statLabel}
                                    dangerouslySetInnerHTML={{ __html: item.label }}
                                />
                                <div className={styles.statValue}>
                                    {item.current} <span className={styles.arrow}>→</span> {item.next}
                                </div>
                                {(data?.score_points ?? 0) > 0 ? (
                                    <button
                                        className={styles.plusBtn}
                                        type="button"
                                        onClick={() => handleAllocate(item.key)}
                                    >
                                        ＋
                                    </button>
                                ) : null}
                            </div>
                        ))}
                        <div className={styles.pointsRow}>
                            <span className={styles.pointsLabel}>ポイント：</span>
                            <span className={styles.pointsValue}>{data?.score_points ?? 0}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div className={styles.scoreFooter}>
                <button
                    className={styles.scoreBtn}
                    type="button"
                    onClick={() => router.push("/auth/")}
                >
                    タイトルに戻る
                </button>
                <button
                    className={styles.scoreBtn}
                    type="button"
                    onClick={() => router.push("/game/start")}
                >
                    続けてプレイ
                </button>
            </div>
        </div>
    );
}
