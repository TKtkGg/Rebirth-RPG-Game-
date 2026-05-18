"use client"
import { useEffect, useState } from "react";
import { apiGet } from "../../lib/apiClient";
import { StagesScreenData } from "../types/stage_types";
import { useRouter } from "next/navigation";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import styles from "./StagesScreen.module.css";
import { StageButton } from "@/src/components/Organisms/stage/StageButton";

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
                    return <StageButton key={stage.id} stage={stage} playerLevel={data?.player.level ?? 0} playerId={playerId} />
                })}
                <ReturnButton
                    className={styles.backButton}
                    onClick={() => router.push(`/game/battle/home/${playerId}`)}
                />
            </div>
        </div>
    )
}