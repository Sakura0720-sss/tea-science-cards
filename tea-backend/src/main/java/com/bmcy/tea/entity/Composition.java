package com.bmcy.tea.entity;

import jakarta.persistence.*;

/**
 * 茶叶成分，如茶多酚、咖啡碱、氨基酸、儿茶素等。
 * 通过 teaProductId 关联茶品，一个茶品可有多种成分。
 */
@Entity
@Table(name = "composition")
public class Composition {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 关联茶品 id */
    private Long teaProductId;

    /** 成分名称，如「茶多酚」 */
    private String name;

    /** 数值 */
    private Double value;

    /** 单位，如 %、mg/g */
    private String unit;

    public Composition() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTeaProductId() { return teaProductId; }
    public void setTeaProductId(Long teaProductId) { this.teaProductId = teaProductId; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Double getValue() { return value; }
    public void setValue(Double value) { this.value = value; }
    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }
}
