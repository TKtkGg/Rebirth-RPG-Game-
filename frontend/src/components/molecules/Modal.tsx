import styles from "./Modal.module.css";

type Props = {
    setIsModalOpen: (open: boolean) => void;
    children: React.ReactNode;
    className?: string;
}

export default function Modal(props: Props) {
    const { setIsModalOpen, children, className } = props;
    return (
        <div className={`${styles.modalOverlay} ${className || ""}`} onClick={() => setIsModalOpen(false)}>
            {children}
        </div>
    );
}