import styles from "./SideTabs.module.css";

type Props = {
    questType: "life" | "account";
    setQuestType: (questType: "life" | "account") => void;
    isGuest: boolean;
}

export default function SideTabs(props: Props) {
    const { questType, setQuestType, isGuest } = props;

    const tabButton = (label: string, value: "life" | "account") => {
        return (
            <button
                type="button"
                className={`${styles.questTab} ${questType === value ? styles.active : ""} ${value === "account" && isGuest ? styles.disabled : ""}`}
                disabled={value === "account" && isGuest}
                onClick={() => setQuestType(value)}
            >
                {label}
            </button>
        )
    }

    return (
        <div className={styles.sidebar}>
            {tabButton("ライフ", "life")}
            {tabButton("アカウント", "account")}
        </div>
    )
}