package com.bmcy.tea.entity;

import jakarta.persistence.*;

/**
 * 风味词汇及多语言翻译。
 * 一个风味词（如「松烟香」）可存多语言对照，供前端多语言切换使用。
 */
@Entity
@Table(name = "flavor")
public class Flavor {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 关联茶品 id */
    private Long teaProductId;

    /** 风味词原文（中文），如「松烟香」 */
    private String termZh;

    /** 英文翻译 */
    private String termEn;

    /** 其他语言翻译（JSON 字符串，预留扩展） */
    @Column(length = 2000)
    private String translations;

    public Flavor() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTeaProductId() { return teaProductId; }
    public void setTeaProductId(Long teaProductId) { this.teaProductId = teaProductId; }
    public String getTermZh() { return termZh; }
    public void setTermZh(String termZh) { this.termZh = termZh; }
    public String getTermEn() { return termEn; }
    public void setTermEn(String termEn) { this.termEn = termEn; }
    public String getTranslations() { return translations; }
    public void setTranslations(String translations) { this.translations = translations; }
}
