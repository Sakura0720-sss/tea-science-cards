package com.bmcy.tea.controller;

import com.bmcy.tea.entity.Composition;
import com.bmcy.tea.entity.Flavor;
import com.bmcy.tea.entity.TeaProduct;
import com.bmcy.tea.repository.CompositionRepository;
import com.bmcy.tea.repository.FlavorRepository;
import com.bmcy.tea.repository.TeaProductRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 茶品、成分、风味的查询与维护接口。
 */
@RestController
@RequestMapping("/api/tea")
public class TeaController {

    private final TeaProductRepository teaRepo;
    private final CompositionRepository compRepo;
    private final FlavorRepository flavorRepo;

    public TeaController(TeaProductRepository teaRepo,
                         CompositionRepository compRepo,
                         FlavorRepository flavorRepo) {
        this.teaRepo = teaRepo;
        this.compRepo = compRepo;
        this.flavorRepo = flavorRepo;
    }

    // ===== 茶品 =====

    @GetMapping
    public List<TeaProduct> list(@RequestParam(required = false) String category) {
        if (category != null && !category.isBlank()) {
            return teaRepo.findByCategory(category);
        }
        return teaRepo.findAll();
    }

    @GetMapping("/search")
    public List<TeaProduct> search(@RequestParam String keyword) {
        return teaRepo.findByNameZhContaining(keyword);
    }

    @PostMapping
    public TeaProduct create(@RequestBody TeaProduct tea) {
        return teaRepo.save(tea);
    }

    /** 更新茶品信息（补充产地/工艺/香气等） */
    @PutMapping("/{id}")
    public TeaProduct update(@PathVariable Long id, @RequestBody TeaProduct tea) {
        TeaProduct existing = teaRepo.findById(id).orElseThrow(() -> new RuntimeException("茶品不存在"));
        if (tea.getNameZh() != null) existing.setNameZh(tea.getNameZh());
        if (tea.getNameEn() != null) existing.setNameEn(tea.getNameEn());
        if (tea.getCategory() != null) existing.setCategory(tea.getCategory());
        if (tea.getStdNo() != null) existing.setStdNo(tea.getStdNo());
        if (tea.getOrigin() != null) existing.setOrigin(tea.getOrigin());
        if (tea.getProcess() != null) existing.setProcess(tea.getProcess());
        if (tea.getFlavor() != null) existing.setFlavor(tea.getFlavor());
        return teaRepo.save(existing);
    }

    /** 查某茶品的完整信息（含成分、风味） */
    @GetMapping("/{id}/detail")
    public Map<String, Object> detail(@PathVariable Long id) {
        TeaProduct tea = teaRepo.findById(id).orElseThrow(() -> new RuntimeException("茶品不存在"));
        List<Composition> comps = compRepo.findByTeaProductId(id);
        List<Flavor> flavors = flavorRepo.findByTeaProductId(id);
        return Map.of(
            "tea", tea,
            "compositions", comps,
            "flavors", flavors
        );
    }

    // ===== 成分 =====

    @GetMapping("/{teaProductId}/composition")
    public List<Composition> composition(@PathVariable Long teaProductId) {
        return compRepo.findByTeaProductId(teaProductId);
    }

    @PostMapping("/composition")
    public Composition addComposition(@RequestBody Composition comp) {
        return compRepo.save(comp);
    }

    // ===== 风味 =====

    @GetMapping("/{teaProductId}/flavor")
    public List<Flavor> flavor(@PathVariable Long teaProductId) {
        return flavorRepo.findByTeaProductId(teaProductId);
    }

    @PostMapping("/flavor")
    public Flavor addFlavor(@RequestBody Flavor flavor) {
        return flavorRepo.save(flavor);
    }
}
