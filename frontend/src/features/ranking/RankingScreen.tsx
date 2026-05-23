"use client"

import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { RankingData } from "./types";
import { apiGet } from "@/src/lib/apiClient";
import { SectionTitle } from "@/src/components/atoms/title/SectionTitle";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import styles from "./RankingScreen.module.css";
import RankingEntry from "@/src/components/molecules/ranking/RankingEntry";

type Props = {
    playerId: string;
};

const PLACEHOLDER_ENTRY: RankingData["entries"][number] = {
    name: "—",
    value: 0,
    job: "",
    job_icon: "game/img/アイコン/はてな_アイコン.png",
};

const FALLBACK_CATEGORIES: RankingData["categories"] = [
    { key: "score", label: "スコア" },
    { key: "strong", label: "強敵討伐数" },
    { key: "victories", label: "勝利回数" },
];

function toPublicPath(path: string): string {
    if (!path) return "/game/img/アイコン/はてな_アイコン.png";
    return path.startsWith("/") ? path : `/${path}`;
}

export default function RankingScreen({ playerId }: Props) {
    const router = useRouter();
    const [rankingData, setRankingData] = useState<RankingData | null>(null);
    const [category, setCategory] = useState<string>("score");

    useEffect(() => {
        apiGet(`/api/ranking/${playerId}?category=${category}`)
            .then((data: RankingData) => {
                setRankingData(data);
            });
    }, [playerId, category]);

    const categories = rankingData?.categories ?? FALLBACK_CATEGORIES;

    const entries =
        rankingData?.entries && rankingData.entries.length === 3
            ? rankingData.entries
            : [PLACEHOLDER_ENTRY, PLACEHOLDER_ENTRY, PLACEHOLDER_ENTRY];

    const first = entries[0];
    const second = entries[1];
    const third = entries[2];

    const sectionTitle =
        rankingData?.label ?? categories.find((c) => c.key === category)?.label ?? "スコア";

    return (
        <div className={styles.layout}>
            <aside className={styles.sidebar}>
                <div className={styles.sidebarTitle}>ランキング</div>
                {categories.map((cat) => (
                    <button
                        key={cat.key}
                        type="button"
                        className={`${styles.sidebarItem} ${category === cat.key ? styles.sidebarItemActive : ""}`}
                        onClick={() => setCategory(cat.key)}
                    >
                        {cat.label}
                    </button>
                ))}
                <div className={styles.backWrap}>
                    <ReturnButton onClick={() => router.push(`/game/battle/home/${playerId}`)} />
                </div>
            </aside>

            <main className={styles.main}>
                <SectionTitle title={sectionTitle} className={styles.mainTitle} />

                <div className={styles.board}>
                    <Image
                        src="/game/img/アイコン/ランキング台.png"
                        alt="ランキング台"
                        width={900}
                        height={520}
                        className={styles.podiumImage}
                        priority
                    />

                    <RankingEntry value={first.value} name={first.name} job_icon={toPublicPath(first.job_icon)} job={first.job} className={styles.podiumFirst} />
                    <RankingEntry value={second.value} name={second.name} job_icon={toPublicPath(second.job_icon)} job={second.job} className={styles.podiumSecond} />
                    <RankingEntry value={third.value} name={third.name} job_icon={toPublicPath(third.job_icon)} job={third.job} className={styles.podiumThird} />
                </div>
            </main>
        </div>
    );
}
