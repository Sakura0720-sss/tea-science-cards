package com.bmcy.tea.entity;

import jakarta.persistence.*;

/**
 * 茶品。对应六大茶类、地理标志名茶、紧压茶等。
 */
@Entity
@Table(name = "tea_product")
public class TeaProduct {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 标准号，如 GB/T 18650-2008 */
    private String stdNo;

    /** 中文名称，如「龙井茶」 */
    private String nameZh;

    /** 英文名称 */
    private String nameEn;

    /** 茶类：绿茶/红茶/乌龙茶/白茶/黄茶/黑茶/紧压茶等 */
    private String category;

    /** 产地 */
    private String origin;

    /** 工艺描述 */
    @Column(length = 1000)
    private String process;

    /** 香气风味描述 */
    @Column(length = 1000)
    private String flavor;

    public TeaProduct() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getStdNo() { return stdNo; }
    public void setStdNo(String stdNo) { this.stdNo = stdNo; }
    public String getNameZh() { return nameZh; }
    public void setNameZh(String nameZh) { this.nameZh = nameZh; }
    public String getNameEn() { return nameEn; }
    public void setNameEn(String nameEn) { this.nameEn = nameEn; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    public String getOrigin() { return origin; }
    public void setOrigin(String origin) { this.origin = origin; }
    public String getProcess() { return process; }
    public void setProcess(String process) { this.process = process; }
    public String getFlavor() { return flavor; }
    public void setFlavor(String flavor) { this.flavor = flavor; }
}
