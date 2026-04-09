import styles from './title.module.css'

export const SectionTitle = ({ title }: { title: string }) => {
    return(
        <div className={styles.sectionTitle}>
            {title}
        </div>
    )
}