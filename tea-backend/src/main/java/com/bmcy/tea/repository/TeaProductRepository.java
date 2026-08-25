package com.bmcy.tea.repository;

import com.bmcy.tea.entity.TeaProduct;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TeaProductRepository extends JpaRepository<TeaProduct, Long> {
    List<TeaProduct> findByCategory(String category);
    List<TeaProduct> findByNameZhContaining(String keyword);
}
