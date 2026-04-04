import { apiPost } from "../../../lib/apiClient";
import { HomeScreenData } from "../../../features/battle_home/types";

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
                <button onClick={() => {
                    apiPost(`/api/battle_start/${playerId}/`, {
                        stat: stat,
                    }).then((data: HomeScreenData) => {
                        setData(data);
                    });
                }}>+</button>
            )}
        </>
    )
}