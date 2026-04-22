"use client"
import { useEffect, useState } from "react";
import { apiGet } from "../../lib/apiClient";
import { StagesScreenData } from "./types";
import { useRouter } from "next/navigation";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import styles from "./StagesScreen.module.css";

type Props = {
    playerId: string;
}

export default function StagesScreen({ playerId }: Props) {
    const [data, setData] = useState<StagesScreenData | null>(null);
    const router = useRouter();

    useEffect(() => {
        apiGet(`/api/stages/${playerId}`).then((data: StagesScreenData) => {
            setData(data);
        });
    }, [playerId]);

    const sortedStages = [...(data?.stages ?? [])].sort((a, b) => a.order - b.order);

    return(
        <div className={styles.container}>
            <div className={styles.board}>
                {sortedStages.map((stage) => {
                    const isLocked = stage.unlock_level > (data?.player.level ?? 0);
                    return (
                        <button
                            key={stage.id}
                            type="button"
                            className={`${styles.stageButton} ${isLocked ? styles.locked : ""}`}
                            style={{ backgroundImage: `url("/game/img/背景/${stage.background_image}")` }}
                        >
                            {isLocked && (
                                <div className={styles.lockedOverlay}>
                                    <p className={styles.unlockLabel}>開放条件</p>
                                    <p className={styles.unlockText}>レベル{stage.unlock_level}以上</p>
                                </div>
                            )}
                            <p className={styles.stageName}>{stage.name}</p>
                        </button>
                    );
                })}
                <ReturnButton
                    className={styles.backButton}
                    onClick={() => router.push(`/game/battle/home/${playerId}`)}
                />
            </div>
        </div>
    )
}