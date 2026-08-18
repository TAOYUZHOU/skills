(function () {
  "use strict";

  const dataset = window.ROUTE_COMPARE_DATA;
  const state = { index: 0, scale: {} };
  const byId = (id) => document.getElementById(id);
  let svgInstanceCounter = 0;

  function slots() {
    return dataset.slots || [
      { id: "new", kicker: "New", title: "新评分", accent: "new" },
      { id: "old", kicker: "Original", title: "原始", accent: "old" },
    ];
  }

  function routeOf(item, slotId) {
    if (item.routes && item.routes[slotId]) return item.routes[slotId];
    return item[slotId] || null;
  }

  function uniquifyInlineSvgIds(scope) {
    const prefix = `mol-${++svgInstanceCounter}-`;
    const idMap = new Map();
    scope.querySelectorAll("svg [id]").forEach((element) => {
      const oldId = element.id;
      const newId = `${prefix}${oldId}`;
      idMap.set(oldId, newId);
      element.id = newId;
    });
    if (!idMap.size) return;
    scope.querySelectorAll("svg *").forEach((element) => {
      [...element.attributes].forEach((attribute) => {
        let value = attribute.value;
        idMap.forEach((newId, oldId) => {
          if (value === `#${oldId}`) value = `#${newId}`;
          value = value.replaceAll(`url(#${oldId})`, `url(#${newId})`);
        });
        if (value !== attribute.value) element.setAttribute(attribute.name, value);
      });
    });
  }

  function sci(value) {
    if (value === null || value === undefined || !Number.isFinite(value)) return "—";
    return Number(value).toFixed(3);
  }

  function fixed(value, digits) {
    if (value === null || value === undefined || !Number.isFinite(value)) return "—";
    return Number(value).toFixed(digits);
  }

  function compactScore(value) {
    if (value === null || value === undefined || !Number.isFinite(value)) return "—";
    return Number(value) === 1 ? "1" : Number(value).toFixed(3);
  }

  function badge(text, className) {
    const span = document.createElement("span");
    span.className = `node-badge ${className || ""}`.trim();
    span.textContent = text;
    return span;
  }

  function softTerminalRewardBadge(node, fallbackClass) {
    let exponent = "^1";
    let className = fallbackClass || "base";
    if (node.soft_coverage_class === "strong") {
      exponent = "^0.5";
      className = "strong";
    } else if (node.soft_coverage_class === "weak") {
      exponent = "^0.75";
      className = "weak";
    }
    const result = badge(`STR ${exponent}`, className);
    result.title = "Soft-Terminal Reward";
    return result;
  }

  function assignReactionStepLabels(placements) {
    const labels = new WeakMap();
    const branchCounters = {};
    placements
      .filter((placement) => placement.node.kind === "reaction")
      .sort((left, right) => left.depth - right.depth || left.y - right.y)
      .forEach((placement) => {
        const step = Number(placement.depth ?? 0) + 1;
        branchCounters[step] = (branchCounters[step] || 0) + 1;
        const branch = branchCounters[step];
        labels.set(placement.node, step === 1 ? "1" : `${step}.${branch}`);
      });
    return labels;
  }

  function edgeLabelPoint(edge) {
    const startX = edge.source.x + edge.source.width;
    const endX = edge.target.x;
    const bendX = startX + (endX - startX) / 2;
    return { x: bendX, y: edge.source.y };
  }

  function reactionSmilesFromNode(node) {
    if (!node || node.kind !== "reaction") return "";
    if (node.reaction_id && String(node.reaction_id).includes(">>")) return node.reaction_id;
    const product = String(node.smiles || "").trim();
    const reactants = (node.children || [])
      .map((child) => String(child.smiles || "").trim())
      .filter(Boolean);
    if (!product || !reactants.length) return "";
    return `${reactants.join(".")}>>${product}`;
  }

  let rxnPopover = null;
  let rxnPopoverOutsideHandler = null;

  function hideRxnPopover() {
    if (!rxnPopover) return;
    rxnPopover.hidden = true;
    if (rxnPopoverOutsideHandler) {
      document.removeEventListener("click", rxnPopoverOutsideHandler);
      rxnPopoverOutsideHandler = null;
    }
  }

  function ensureRxnPopover() {
    if (rxnPopover) return rxnPopover;
    rxnPopover = document.createElement("div");
    rxnPopover.id = "rxnPopover";
    rxnPopover.className = "rxn-popover";
    rxnPopover.hidden = true;
    rxnPopover.innerHTML = `
      <div class="rxn-popover-head">
        <strong class="rxn-popover-title"></strong>
        <button type="button" class="rxn-popover-close" aria-label="关闭">×</button>
      </div>
      <textarea class="rxn-popover-text" readonly rows="4" spellcheck="false"></textarea>
      <div class="rxn-popover-actions">
        <button type="button" class="rxn-popover-copy">复制 rxn</button>
      </div>
      <div class="rxn-popover-status" aria-live="polite"></div>
    `;
    document.body.appendChild(rxnPopover);
    rxnPopover.querySelector(".rxn-popover-close").addEventListener("click", (event) => {
      event.stopPropagation();
      hideRxnPopover();
    });
    rxnPopover.querySelector(".rxn-popover-copy").addEventListener("click", async (event) => {
      event.stopPropagation();
      const text = rxnPopover.querySelector(".rxn-popover-text").value;
      const status = rxnPopover.querySelector(".rxn-popover-status");
      try {
        await navigator.clipboard.writeText(text);
        status.textContent = "已复制到剪贴板";
      } catch (_error) {
        rxnPopover.querySelector(".rxn-popover-text").focus();
        rxnPopover.querySelector(".rxn-popover-text").select();
        status.textContent = "请手动复制（浏览器未授权剪贴板）";
      }
    });
    rxnPopover.addEventListener("click", (event) => event.stopPropagation());
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") hideRxnPopover();
    });
    return rxnPopover;
  }

  function showRxnPopover(anchor, label, rxn) {
    const popover = ensureRxnPopover();
    popover.querySelector(".rxn-popover-title").textContent = `反应 ${label}`;
    popover.querySelector(".rxn-popover-text").value = rxn;
    popover.querySelector(".rxn-popover-status").textContent = "";
    popover.hidden = false;
    const rect = anchor.getBoundingClientRect();
    popover.style.visibility = "hidden";
    popover.style.left = "0px";
    popover.style.top = "0px";
    const width = popover.offsetWidth;
    const left = Math.max(12, Math.min(rect.left, window.innerWidth - width - 12));
    const top = Math.min(rect.bottom + 8, window.innerHeight - popover.offsetHeight - 12);
    popover.style.left = `${left}px`;
    popover.style.top = `${top}px`;
    popover.style.visibility = "visible";
    if (rxnPopoverOutsideHandler) document.removeEventListener("click", rxnPopoverOutsideHandler);
    rxnPopoverOutsideHandler = () => hideRxnPopover();
    window.setTimeout(() => document.addEventListener("click", rxnPopoverOutsideHandler), 0);
  }

  function nodeDepthLabel(node) {
    return Number.isFinite(Number(node.depth)) ? String(node.depth) : "0";
  }

  function appendReactionStepMarker(stage, point, label, node) {
    const marker = document.createElement("button");
    marker.type = "button";
    marker.className = "reaction-step-marker";
    marker.textContent = label;
    const rxn = reactionSmilesFromNode(node);
    marker.title = rxn
      ? `反应 ${label} · 点击查看并复制 rxn`
      : `反应 ${label}（d=${nodeDepthLabel(node)}）`;
    const width = label.length > 2 ? 34 : 24;
    marker.style.left = `${point.x - width / 2}px`;
    marker.style.top = `${point.y - 12}px`;
    if (label.length > 2) marker.classList.add("wide");
    if (rxn) {
      marker.classList.add("has-rxn");
      marker.addEventListener("click", (event) => {
        event.stopPropagation();
        showRxnPopover(marker, label, rxn);
      });
    } else {
      marker.disabled = true;
    }
    stage.appendChild(marker);
  }

  function createNodeCard(node, isRouteDifference, stepLabel) {
    const card = document.createElement("div");
    const terminalClass = node.kind === "reaction" && node.soft_terminal_class && node.soft_terminal_class !== "none"
      ? `soft-terminal-${node.soft_terminal_class}` : "";
    const coverageClass = node.kind === "reaction" && node.soft_coverage_class && node.soft_coverage_class !== "none"
      ? `soft-covered-${node.soft_coverage_class}` : "";
    const existenceClass = `molecule-${node.molecule_existence || "none"}`;
    card.className = `route-node ${existenceClass} ${node.kind === "leaf" ? "leaf" : ""} ${node.known ? "known" : ""} ${terminalClass} ${coverageClass} ${isRouteDifference ? "route-difference" : ""}`.trim();
    const mol = document.createElement("div");
    mol.className = "mol-box";
    mol.innerHTML = node.svg || "";
    uniquifyInlineSvgIds(mol);
    card.appendChild(mol);
    if (node.kind === "leaf") return card;

    const meta = document.createElement("div");
    meta.className = "node-meta";
    const title = document.createElement("div");
    title.className = "reaction-score-title";
    title.textContent = `反应 ${stepLabel || "—"} · 反应打分 →`;
    meta.appendChild(title);
    const synthBadge = badge(`SA ${compactScore(node.synth_penalty_factor)}`, node.synth_penalty_factor < 1 ? "synth" : "base");
    synthBadge.title = `SynthScore 惩罚；产物=${sci(node.product_synthscore_max)}，最难反应物=${sci(node.reactant_synthscore_max)}`;
    if (node.known) {
      meta.appendChild(badge(`step ${sci(node.new_step_score)}`, "known"));
      meta.appendChild(badge("forward 1", "known"));
      meta.appendChild(badge("sim03 1", "known"));
      meta.appendChild(synthBadge);
      const knownReward = badge("STR ^0.5", "strong");
      knownReward.title = "known 固定按强软显示";
      meta.appendChild(knownReward);
    } else {
      meta.appendChild(badge(`step ${sci(node.new_step_score)}`, "hit"));
      if (node.forward_floor_applied) {
        meta.appendChild(badge(`fwd raw ${compactScore(node.forward_raw_probability)}`, "miss"));
        meta.appendChild(badge(`fwd eff ${compactScore(node.forward_probability)}`, "floor"));
      } else {
        meta.appendChild(badge(`forward ${compactScore(node.forward_probability)}`, "hit"));
      }
      meta.appendChild(badge(`sim03 ${compactScore(node.similarity_factor)}`, "sim"));
      meta.appendChild(synthBadge);
      meta.appendChild(softTerminalRewardBadge(node, "base"));
    }
    card.appendChild(meta);
    return card;
  }

  const treeLayout = {
    reactionWidth: 334,
    leafWidth: 230,
    reactionHeight: 190,
    leafHeight: 156,
    columnPitch: 426,
    interBranchGap: 24,
    siblingReactantGap: 12,
    paddingX: 38,
    paddingY: 32,
  };

  function nodeSize(node) {
    return node.kind === "leaf"
      ? { width: treeLayout.leafWidth, height: treeLayout.leafHeight }
      : { width: treeLayout.reactionWidth, height: treeLayout.reactionHeight };
  }

  function buildContourLayout(node, depth) {
    const size = nodeSize(node);
    const children = node.children || [];
    const rootPlacement = { node, depth, y: 0, width: size.width, height: size.height };
    if (!children.length) {
      return {
        placements: [rootPlacement],
        contours: [{ min: -size.height / 2, max: size.height / 2 }],
      };
    }
    const childLayouts = children.map((child) => buildContourLayout(child, depth + 1));
    const combinedContours = [];
    const childOffsets = [];
    const childPlacements = [];
    childLayouts.forEach((layout, index) => {
      let offset = 0;
      if (index > 0) {
        layout.contours.forEach((contour, level) => {
          const occupied = combinedContours[level];
          if (occupied) {
            const gap = level === 0 ? treeLayout.siblingReactantGap : treeLayout.interBranchGap;
            offset = Math.max(offset, occupied.max + gap - contour.min);
          }
        });
      }
      childOffsets.push(offset);
      layout.placements.forEach((placement) => {
        childPlacements.push({ ...placement, y: placement.y + offset });
      });
      layout.contours.forEach((contour, level) => {
        const shifted = { min: contour.min + offset, max: contour.max + offset };
        if (!combinedContours[level]) combinedContours[level] = shifted;
        else {
          combinedContours[level].min = Math.min(combinedContours[level].min, shifted.min);
          combinedContours[level].max = Math.max(combinedContours[level].max, shifted.max);
        }
      });
    });
    const center = (childOffsets[0] + childOffsets[childOffsets.length - 1]) / 2;
    childPlacements.forEach((placement) => { placement.y -= center; });
    const contours = [{ min: -size.height / 2, max: size.height / 2 }];
    combinedContours.forEach((contour, level) => {
      contours[level + 1] = { min: contour.min - center, max: contour.max - center };
    });
    return { placements: [rootPlacement, ...childPlacements], contours };
  }

  function compactTreeLayout(root) {
    const layout = buildContourLayout(root, 0);
    const minY = Math.min(...layout.placements.map((item) => item.y - item.height / 2));
    const maxY = Math.max(...layout.placements.map((item) => item.y + item.height / 2));
    layout.placements.forEach((item) => {
      item.x = treeLayout.paddingX + item.depth * treeLayout.columnPitch;
      item.y = treeLayout.paddingY + item.y - minY;
    });
    const byNode = new Map(layout.placements.map((item) => [item.node, item]));
    const edges = [];
    const stack = [root];
    while (stack.length) {
      const parent = stack.pop();
      (parent.children || []).forEach((child) => {
        edges.push({ source: byNode.get(parent), target: byNode.get(child), known: Boolean(parent.known) });
        stack.push(child);
      });
    }
    const maxX = Math.max(...layout.placements.map((item) => item.x + item.width));
    return {
      placements: layout.placements,
      edges,
      width: maxX + treeLayout.paddingX,
      height: maxY - minY + treeLayout.paddingY * 2,
    };
  }

  function connectorPath(edge) {
    const startX = edge.source.x + edge.source.width;
    const endX = edge.target.x;
    const bendX = startX + (endX - startX) / 2;
    return `M ${startX} ${edge.source.y} H ${bendX} V ${edge.target.y} H ${endX}`;
  }

  function flattenTree(root) {
    const nodes = [];
    const stack = [root];
    while (stack.length) {
      const node = stack.pop();
      nodes.push(node);
      const children = node.children || [];
      for (let index = children.length - 1; index >= 0; index -= 1) stack.push(children[index]);
    }
    return nodes;
  }

  function reactionDifferenceMoleculeNodes(route, otherRoutes) {
    const available = new Map();
    otherRoutes.forEach((other) => {
      if (!other?.tree) return;
      flattenTree(other.tree).forEach((node) => {
        if (node.kind !== "reaction") return;
        const key = node.reaction_id || "";
        available.set(key, (available.get(key) || 0) + 1);
      });
    });
    const highlightedMolecules = new WeakSet();
    if (!route?.tree) return highlightedMolecules;
    flattenTree(route.tree).forEach((node) => {
      if (node.kind !== "reaction") return;
      const key = node.reaction_id || "";
      if ((available.get(key) || 0) > 0) return;
      highlightedMolecules.add(node);
      (node.children || []).forEach((reactantNode) => highlightedMolecules.add(reactantNode));
    });
    return highlightedMolecules;
  }

  function renderTree(stage, route, differenceNodes) {
    hideRxnPopover();
    stage.textContent = "";
    if (!route?.tree) {
      stage.textContent = "无路线";
      return;
    }
    stage.classList.add("compact-layout");
    const layout = compactTreeLayout(route.tree);
    const stepLabels = assignReactionStepLabels(layout.placements);
    const width = Math.max(1450, layout.width);
    const height = Math.max(500, layout.height);
    stage.style.width = `${width}px`;
    stage.style.minWidth = `${width}px`;
    stage.style.height = `${height}px`;
    stage.setAttribute("role", "tree");

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("route-connectors");
    svg.setAttribute("width", String(width));
    svg.setAttribute("height", String(height));
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("aria-hidden", "true");
    layout.edges.forEach((edge) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", connectorPath(edge));
      path.setAttribute("class", `route-edge${edge.known ? " known" : ""}`);
      svg.appendChild(path);
    });
    stage.appendChild(svg);

    layout.placements.forEach((placement) => {
      const wrapper = document.createElement("div");
      wrapper.className = "compact-tree-node";
      wrapper.style.left = `${placement.x}px`;
      wrapper.style.top = `${placement.y - placement.height / 2}px`;
      wrapper.setAttribute("role", "treeitem");
      const stepLabel = stepLabels.get(placement.node) || "";
      wrapper.appendChild(createNodeCard(placement.node, differenceNodes.has(placement.node), stepLabel));
      stage.appendChild(wrapper);
    });

    layout.placements.forEach((placement) => {
      if (placement.node.kind !== "reaction") return;
      const label = stepLabels.get(placement.node);
      if (!label) return;
      const outgoing = layout.edges
        .filter((edge) => edge.source.node === placement.node)
        .sort((left, right) => left.target.y - right.target.y);
      if (!outgoing.length) return;
      appendReactionStepMarker(stage, edgeLabelPoint(outgoing[0]), label, placement.node);
    });
  }

  function revealRoot(stage) {
    const canvas = stage.parentElement;
    const rootCard = stage.querySelector(".route-node");
    if (!canvas || !rootCard) return;
    const canvasBox = canvas.getBoundingClientRect();
    const cardBox = rootCard.getBoundingClientRect();
    canvas.scrollLeft = 0;
    canvas.scrollTop = Math.max(0, canvas.scrollTop + cardBox.top - canvasBox.top - 90);
  }

  function statPill(text, primary) {
    const span = document.createElement("span");
    span.className = `stat-pill${primary ? " primary" : ""}`;
    span.textContent = text;
    return span;
  }

  function renderStats(container, route, primary) {
    container.textContent = "";
    if (!route) return;
    container.appendChild(statPill(`logS ${fixed(route.new_log_score, 3)}`, primary));
    if (route.old_score0 !== undefined && route.old_score0 !== null) {
      container.appendChild(statPill(`score0 ${fixed(route.old_score0, 5)}`));
    }
    if (route.steps != null) container.appendChild(statPill(`${route.steps} steps`));
    if (route.known_steps != null) container.appendChild(statPill(`known ${route.known_steps}`));
    (route.pills || []).forEach((text) => container.appendChild(statPill(text)));
  }

  function ensurePanels() {
    const grid = byId("comparisonGrid");
    if (grid.dataset.ready === "1") return;
    slots().forEach((slot) => {
      const article = document.createElement("article");
      article.id = `${slot.id}Panel`;
      article.className = `route-panel route-panel-${slot.accent || "old"}`;
      article.innerHTML = `
        <header class="panel-head">
          <div>
            <p class="panel-kicker">${slot.kicker || ""}</p>
            <h2>${slot.title || slot.id}</h2>
          </div>
          <div id="${slot.id}Stats" class="panel-stats"></div>
          <div class="zoom-controls" aria-label="${slot.id} 缩放">
            <button type="button" data-panel="${slot.id}" data-zoom="out">−</button>
            <button type="button" data-panel="${slot.id}" data-zoom="in">+</button>
            <button type="button" data-panel="${slot.id}" data-zoom="reset">复位</button>
          </div>
        </header>
        <div class="legend">
          <span><i class="swatch purchasable"></i>绿框：已知/可购买原料</span>
          <span><i class="swatch reaction-dataset"></i>紫框：反应库已知物</span>
          <span><i class="swatch pubchem"></i>青框：PubChem 已知物</span>
          <span><i class="swatch route-difference"></i>淡红底：该面板独有反应</span>
          <span><i class="swatch known-line"></i>已知反应</span>
          <span><i class="swatch step-no"></i>反应编号：点击可复制 rxn</span>
        </div>
        <div class="route-canvas"><div id="${slot.id}Stage" class="route-stage"></div></div>
      `;
      grid.appendChild(article);
      state.scale[slot.id] = 1;
    });
    grid.dataset.ready = "1";
  }

  function renderCaseList() {
    const list = byId("caseList");
    list.textContent = "";
    dataset.cases.forEach((item, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `case-button${index === state.index ? " active" : ""}`;
      button.textContent = item.target_id;
      button.addEventListener("click", () => {
        goToCase(index);
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      list.appendChild(button);
    });
  }

  function goToCase(index) {
    if (index < 0 || index >= dataset.cases.length || index === state.index) return;
    state.index = index;
    render();
  }

  function render() {
    const item = dataset.cases[state.index];
    byId("caseTitle").textContent = item.target_id;
    byId("progress").textContent = `${state.index + 1} / ${dataset.cases.length}`;
    byId("targetSelect").value = String(state.index);
    byId("prevBtn").disabled = state.index === 0;
    byId("nextBtn").disabled = state.index === dataset.cases.length - 1;
    const targetMol = byId("targetMol");
    targetMol.className = `target-molecule molecule-${item.target_molecule_existence || "none"}`;
    targetMol.innerHTML = item.target_svg || "";
    uniquifyInlineSvgIds(targetMol);

    const shift = byId("shiftSummary");
    shift.textContent = "";
    (item.metrics || []).forEach((text) => {
      const span = document.createElement("span");
      span.className = "metric";
      span.textContent = text;
      shift.appendChild(span);
    });

    const downloads = byId("caseDownloads");
    downloads.textContent = "";
    (item.downloads || []).forEach((row) => {
      const a = document.createElement("a");
      a.href = row.href;
      a.textContent = row.label;
      downloads.appendChild(a);
    });

    const present = slots().map((slot) => ({ slot, route: routeOf(item, slot.id) }));
    present.forEach(({ slot, route }) => {
      const others = present.filter((row) => row.slot.id !== slot.id).map((row) => row.route);
      const diffs = reactionDifferenceMoleculeNodes(route, others);
      renderStats(byId(`${slot.id}Stats`), route, slot.accent === "new");
      const stage = byId(`${slot.id}Stage`);
      renderTree(stage, route, diffs);
      state.scale[slot.id] = 1;
      stage.style.transform = "scale(1)";
      revealRoot(stage);
    });
    renderCaseList();
  }

  function initialize() {
    if (!dataset || !dataset.cases || !dataset.cases.length) {
      byId("caseTitle").textContent = "数据加载失败";
      return;
    }
    document.title = dataset.title || "Route comparison";
    byId("pageTitle").textContent = dataset.title || "评分路线对照";
    byId("eyebrow").textContent = dataset.eyebrow || "Retro Engine";
    byId("lede").textContent = dataset.lede || "";
    if (dataset.formula) byId("formulaNote").textContent = dataset.formula;
    const actions = byId("heroActions");
    (dataset.links || []).forEach((row) => {
      const a = document.createElement("a");
      a.href = row.href;
      a.textContent = row.label;
      if (row.primary) a.className = "primary";
      actions.appendChild(a);
    });
    byId("caseListCount").textContent = String(dataset.cases.length);
    ensurePanels();
    const select = byId("targetSelect");
    dataset.cases.forEach((item, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = item.target_id;
      select.appendChild(option);
    });
    select.addEventListener("change", () => goToCase(Number(select.value)));
    byId("prevBtn").addEventListener("click", () => {
      if (state.index > 0) goToCase(state.index - 1);
    });
    byId("nextBtn").addEventListener("click", () => {
      if (state.index < dataset.cases.length - 1) goToCase(state.index + 1);
    });
    document.querySelectorAll("[data-zoom]").forEach((button) => {
      button.addEventListener("click", () => {
        const panel = button.dataset.panel;
        const action = button.dataset.zoom;
        if (action === "in") state.scale[panel] = Math.min(2.2, (state.scale[panel] || 1) + 0.12);
        if (action === "out") state.scale[panel] = Math.max(0.35, (state.scale[panel] || 1) - 0.12);
        if (action === "reset") state.scale[panel] = 1;
        byId(`${panel}Stage`).style.transform = `scale(${state.scale[panel]})`;
      });
    });
    render();
  }

  initialize();
})();
