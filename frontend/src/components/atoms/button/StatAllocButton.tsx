import { apiPost } from "../../../lib/apiClient";
import { HomeScreenData } from "../../../features/battle_home/types";
import styles from "./StatAllocButton.module.css";

type Props = {
    "playerId": string
    "stat": string;
    "stat_points": number;
    "setData": (data: HomeScreenData) => void;
}

export default function StatAllocButton(props: Props) {
    const { playerId, stat, stat_points, setData  } = props;
    return(
        <>
            {stat_points > 0 && (
                <button type="button" onClick={() => {
                    apiPost(`/api/battle_start/${playerId}/`, {
                        stat: stat,
                    }).then((data: HomeScreenData) => {
                        setData(data);
                    });
                }} className={styles.statPlus}>＋</button>
            )}
        </>
    )
}