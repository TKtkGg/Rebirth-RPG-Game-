"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { HomeScreenData } from "./types";
import StatAllocButton from "../../components/atoms/button/StatAllocButton";

type Props = {
    "playerId": string 
}

export default function HomeScreen(props: Props) {
    const { playerId } = props;
    const router = useRouter();
    const [data, setData] = useState<HomeScreenData | null>(null);
    const [restText, setRestText] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    useEffect(() => {
        apiGet(`/api/battle_start/${playerId}/`).then((data: HomeScreenData) => {
            setData(data);
        });
    }, [playerId])
    return (
        <div>
            <h1>ホーム</h1>
            <h1>名前：{data?.name}</h1>
            <h1>ジョブ：{data?.job}</h1>
            <h1>レベル：{data?.level}</h1>
            <h1>経験値：{data?.exp_percent}%</h1>
            <h1>所持金：{data?.gold}</h1>

            <h1>HP：{data?.hp} / {data?.max_hp}</h1>
            <StatAllocButton playerId={playerId} stat="hp" stat_points={data?.stat_points || 0} setData={setData} />
            <h1>ATK：{data?.atk}</h1>
            <StatAllocButton playerId={playerId} stat="atk" stat_points={data?.stat_points || 0} setData={setData} />
            <h1>DEF：{data?.defense}</h1>
            <StatAllocButton playerId={playerId} stat="defense" stat_points={data?.stat_points || 0} setData={setData} />
            <h1>SPD：{data?.spd}</h1>
            <StatAllocButton playerId={playerId} stat="spd" stat_points={data?.stat_points || 0} setData={setData} />
            <h1>MP：{data?.mp} / {data?.max_mp}</h1>
            <StatAllocButton playerId={playerId} stat="mp" stat_points={data?.stat_points || 0} setData={setData} />
            <h1>残りポイント：{data?.stat_points}</h1>
            <h1>残りコンテニュー回数：{2 - (data?.death_count || 0)}</h1>

            <button onClick={() => {
                apiPost(`/api/battle_start/${playerId}/`, {
                    action: 'rest',
                }).then((data: HomeScreenData) => {
                    setData(data);
                }).catch((error: { message: string }) => {
                    setRestText(error.message);
                });
            }}>休む</button>
            <p>{restText}</p>
            <button onClick={() => {
                router.push(`/game/stages/`);
            }}>ステージ選択</button>

            <button onClick={() => {
                apiPost(`/api/auth/logout/`, {}).then((data: { ok: boolean }) => {
                    if (data.ok) {
                        localStorage.removeItem('playerId');
                        router.push('/auth/');
                    }
                }).catch((error: { message: string }) => {
                    setErrorMessage(error.message);
                });
            }}>ログアウト</button>
            <p>{errorMessage}</p>
        </div>
    );
}