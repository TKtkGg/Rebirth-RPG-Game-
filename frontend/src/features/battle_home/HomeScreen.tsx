"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { HomeScreenData } from "./types";
import StatAllocButton from "../../components/atoms/button/StatAllocButton";
import { MainPanel } from "@/src/components/atoms/panel/MainPanel";
import styles from "./HomeScreen.module.css";

type Props = {
    playerId: string;
};

function clampPercent(n: number | undefined) {
    if (n == null || Number.isNaN(n)) return 0;
    return Math.min(100, Math.max(0, n));
}

export default function HomeScreen(props: Props) {
    const { playerId } = props;
    const router = useRouter();
    const [data, setData] = useState<HomeScreenData | null>(null);
    const [restText, setRestText] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        apiGet(`/api/battle_start/${playerId}/`).then((d: HomeScreenData) => {
            setData(d);
        });
    }, [playerId]);

    const expPct = clampPercent(data?.exp_percent);

    return (
        <div className={styles.homeRoot}>
            <MainPanel
                state="normal"
                interactive={false}
                className={styles.statusPanel}
            >
                {!data ? (
                    <p className={styles.loading}>読み込み中…</p>
                ) : (
                    <>
                        <div className={styles.statusTitle}>
                            名前：{data.name} 職業：{data.job}
                        </div>

                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>レベル：{data.level}</span>
                        </div>

                        <div className={styles.expBlock}>
                            <div className={styles.expBarLabel}>
                                経験値：{data.exp} / {data.next_exp}
                            </div>
                            <div className={styles.expBar} role="progressbar" aria-valuenow={expPct} aria-valuemin={0} aria-valuemax={100}>
                                <div
                                    className={styles.expBarFill}
                                    style={{ width: `${expPct}%` }}
                                />
                            </div>
                        </div>

                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>所持金：{data.gold}G</span>
                        </div>

                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>
                                HP：{data.total_hp_battle} / {data.total_max_hp_battle}
                            </span>
                            <StatAllocButton playerId={playerId} stat="hp" stat_points={data.stat_points} setData={setData} />
                        </div>
                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>ATK：{data.total_atk_battle}</span>
                            <StatAllocButton playerId={playerId} stat="atk" stat_points={data.stat_points} setData={setData} />
                        </div>
                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>DEF：{data.total_def_battle}</span>
                            <StatAllocButton playerId={playerId} stat="defense" stat_points={data.stat_points} setData={setData} />
                        </div>
                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>SPD：{data.total_spd_battle}</span>
                            <StatAllocButton playerId={playerId} stat="spd" stat_points={data.stat_points} setData={setData} />
                        </div>
                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>
                                SP：{data.mp} / {data.max_mp}
                            </span>
                            <StatAllocButton playerId={playerId} stat="mp" stat_points={data.stat_points} setData={setData} />
                        </div>

                        <div className={styles.statusRow}>
                            <span className={styles.statusLabel}>残りポイント：{data.stat_points}</span>
                        </div>

                        <div className={styles.equipmentDivider}>
                            <div className={styles.statusRow}>
                                <span className={styles.statusLabel}>武器：{data.weapon || "なし"}</span>
                            </div>
                            <div className={styles.statusRow}>
                                <span className={styles.statusLabel}>防具：{data.armor || "なし"}</span>
                            </div>
                        </div>
                    </>
                )}
            </MainPanel>

            <div className={styles.buttonColumn}>
                <button
                    type="button"
                    className={styles.adventureBtn}
                    disabled={!data}
                    onClick={() => router.push("/game/stages/")}
                >
                    <span>冒険</span>
                    <span className={styles.adventureNote}>
                        残り復活回数：{data?.continue_count ?? "—"}回
                    </span>
                </button>

                <button type="button" className={styles.shopBtn}>
                    ショップ
                </button>

                <button
                    type="button"
                    className={styles.restBtn}
                    disabled={!data}
                    onClick={() => {
                        setRestText("");
                        apiPost(`/api/battle_start/${playerId}/`, {
                            action: "rest",
                        })
                            .then((d: HomeScreenData) => {
                                setData(d);
                            })
                            .catch((error: { message: string }) => {
                                setRestText(error.message);
                            });
                    }}
                >
                    休む
                </button>
                {restText ? <p className={styles.restMessage}>{restText}</p> : null}
            </div>

            <button
                type="button"
                className={styles.logoutBtn}
                onClick={() => {
                    setErrorMessage("");
                    apiPost(`/api/auth/logout/`, {})
                        .then((d: { ok: boolean }) => {
                            if (d.ok) {
                                localStorage.removeItem("playerId");
                                router.push("/auth/");
                            }
                        })
                        .catch((error: { message: string }) => {
                            setErrorMessage(error.message);
                        });
                }}
            >
                ログアウト
            </button>
            {errorMessage ? <p className={styles.logoutError}>{errorMessage}</p> : null}
        </div>
    );
}
