"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { StartScreenData } from "./types";
import Image from "next/image";

export default function StartScreen() {
    const router = useRouter();
    const [data, setData] = useState<StartScreenData | null>(null);
    const [name, setName] = useState<string>("");
    const [selectedJob, setSelectedJob] = useState<string>("");
    const [errorMessage, setErrorMessage] = useState("");
    useEffect(() => {
        apiGet('/api/start/').then((data: StartScreenData) => {
            setData(data);
            setName(data?.default_name || "");
        }).catch((error: { message: string }) => {
            setErrorMessage(error.message);
        });
    }, []);
    return (
        <div>
            <input type="text" placeholder="名前を入力" value={name} onChange={(e) => setName(e.target.value)} />
            {data?.job_slots.map((job: StartScreenData["job_slots"][number], index: number) =>
            (
                <button key={index} onClick={() => setSelectedJob(job.name) } disabled={!job.unlocked} style={{ backgroundColor: selectedJob === job.name ? "gray" : "black" }}>
                    <img src={job.icon} alt={job.name} />
                    <p>{job.name}</p>
                    <p>{job.description}</p>
                    <p>{job.bonus}</p>
                </button>
            ))}
            <button onClick={() => {
                if (name === "" && selectedJob === "") {
                    setErrorMessage("名前と職業を選択してください");
                    return;
                }
                else if (name === "") {
                    setErrorMessage("名前を選択してください");
                    return;
                }
                else if (selectedJob === "") {
                    setErrorMessage("職業を選択してください");
                    return;
                }
                apiPost('/api/start/', {
                    name: name,
                    job: selectedJob,
                }).then((data: { player_id: string }) => {
                    const playerId = data.player_id;
                    localStorage.setItem('playerId', playerId)
                    router.push(`/game/battle/home/${playerId}`);
                }).catch((error: { message: string }) => {
                    setErrorMessage(error.message);
                });
                
            }}>スタート</button>
            <p>{errorMessage}</p>
        </div>
    )
}