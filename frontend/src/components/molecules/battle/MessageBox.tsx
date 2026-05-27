import styles from "./MessageBox.module.css";

type Props = {
    message: string;
}

export const MessageBox = (props: Props) => {
    const { message } = props;
    return (
        <div className={styles.messageArea}>
            <div className={styles.messageItem}>
                {message}
            </div>
        </div>
    )
};