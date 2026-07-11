/*
 * app.js
 * Logica del cliente del Editor de EntityScript.
 *
 * IMPORTANTE (decision de arquitectura): este archivo NO tokeniza, NO parsea,
 * NO analiza tipos, NO genera Luau. Su unica responsabilidad es:
 *   1. Mostrar el textarea con numeros de linea.
 *   2. Mandar el texto al servidor local (POST /compile).
 *   3. Mostrar la respuesta (Luau generado o error) tal cual la devuelve
 *      el UNICO compilador real, que vive en Compiler/ (Python).
 *
 * Si en el futuro se agrega una feature al lenguaje, este archivo NO se
 * toca -- el cambio va en Compiler/, y esta interfaz automaticamente lo
 * refleja porque solo reenvia texto y muestra resultados.
 */

(function () {
  const codeArea = document.getElementById("codeArea");
  const lineNumbers = document.getElementById("lineNumbers");
  const output = document.getElementById("output");
  const statusbar = document.getElementById("statusbar");
  const charCount = document.getElementById("charCount");
  const btnCompile = document.getElementById("btnCompile");
  const btnDownload = document.getElementById("btnDownload");
  const btnExample = document.getElementById("btnExample");
  const chkAutoCompile = document.getElementById("chkAutoCompile");
  const chkPreserveComments = document.getElementById("chkPreserveComments");

  let compileTimer = null;

  const EXAMPLES = {
    "01 - Coin (básico)": `entity Coin {
    value = 10

    on touch(player) {
        give player value
        destroy self
    }
}
`,
    "02 - Herencia + daño": `entity Character {
    health = 100
    maxHealth = 100
}

# Los goblins son enemigos basicos: poca vida, sin loot especial.
entity Goblin extends Character {
    @respawnable(15)

    on spawn {
        health = maxHealth
    }

    on damage(amount, source) {
        health -= amount

        if health <= 0 {
            emit EnemyDefeated(self)
            destroy self
        } else {
            play "rbxassetid://9990001"
        }
    }
}
`,
    "03 - Leaderstats + score + funciones": `leaderstat Coins = 0
leaderstat Wins = 0

entity Coin {
    const RespawnDelay = 3
    value = 10
    score = Coins

    position = (0, 3, 0)
    color = "#FFD700"
    anchored = true
    collision = false

    function Collect(player) {
        give player value
        destroy self
    }

    on touch(player) {
        Collect(player)
    }
}

entity GameManager {
    @global

    on join(player) {
        message player "Bienvenido al juego!"
    }

    on timer(seconds) {
        for player in players {
            message player "Segui jugando!"
        }
    }
}
`,
    "04 - NPC con timers": `entity NPCVendor {
    const MaxGreets = 3
    greetCount = 0

    on interact(player) {
        greetCount += 1
        message player "Bienvenido al mercado, viajero."

        if greetCount > MaxGreets {
            give player 5
        }
    }

    function PlaySound() {
        play "rbxassetid://5551234"
    }

    on timer(seconds) {
        after 2 {
            PlaySound()
        }
    }
}
`,
  };

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function updateLineNumbers() {
    const lines = codeArea.value.split("\n").length;
    let nums = "";
    for (let i = 1; i <= lines; i++) nums += i + "\n";
    lineNumbers.textContent = nums;
  }

  function syncScroll() {
    lineNumbers.scrollTop = codeArea.scrollTop;
  }

  codeArea.addEventListener("input", () => {
    updateLineNumbers();
    charCount.textContent = codeArea.value.length + " caracteres";
    if (chkAutoCompile.checked) {
      clearTimeout(compileTimer);
      compileTimer = setTimeout(compile, 500);
    }
  });
  codeArea.addEventListener("scroll", syncScroll);

  codeArea.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = codeArea.selectionStart, end = codeArea.selectionEnd;
      codeArea.value = codeArea.value.slice(0, start) + "    " + codeArea.value.slice(end);
      codeArea.selectionStart = codeArea.selectionEnd = start + 4;
      codeArea.dispatchEvent(new Event("input"));
    }
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      compile();
    }
  });

  // ---------------- Comunicacion con el compilador real (servidor local) ----------------

  async function compile() {
    const source = codeArea.value;

    if (!source.trim()) {
      output.innerHTML = '<div class="placeholder">Escribí código EntityScript a la izquierda y presioná "▶ Compilar".</div>';
      setStatus("Listo.", "ok");
      btnDownload.disabled = true;
      return;
    }

    setStatus("Compilando…", "ok");

    let response;
    try {
      response = await fetch("/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source,
          preserve_comments: chkPreserveComments.checked,
        }),
      });
    } catch (err) {
      output.innerHTML = `<div class="msg-error">
        <div class="msg-title">✗ No se pudo conectar con el servidor local</div>
        <div>Verificá que Editor/webapp/server.py siga corriendo en esta terminal.</div>
      </div>`;
      setStatus("✗ Sin conexión al compilador", "error");
      btnDownload.disabled = true;
      return;
    }

    const data = await response.json();

    if (!data.ok) {
      renderError(data.error, source);
      btnDownload.disabled = true;
      return;
    }

    renderSuccess(data.entities, data.leaderstats, data.warnings);
    btnDownload.disabled = false;
  }

  function renderSuccess(entities, leaderstatsCode, warnings) {
    const names = Object.keys(entities);
    let html = `<div class="msg-success">✓ Compilación exitosa: ${names.length} entidad(es) generada(s).</div>`;

    if (warnings && warnings.length) {
      for (const w of warnings) {
        html += `<div class="msg-warning">⚠ ${escapeHtml(w)}</div>`;
      }
    }

    if (leaderstatsCode) {
      html += fileBlock("LeaderstatsSetup.luau (pegar en ServerScriptService)", leaderstatsCode);
    }
    for (const name of names) {
      html += fileBlock(name + ".luau", entities[name]);
    }

    output.innerHTML = html;
    output.querySelectorAll(".copy-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        navigator.clipboard.writeText(btn.dataset.code);
        btn.textContent = "Copiado!";
        setTimeout(() => (btn.textContent = "Copiar"), 1200);
      });
    });

    setStatus(`✓ Compilado sin errores — ${names.length} archivo(s) Luau listo(s).`, warnings && warnings.length ? "warning" : "ok");
  }

  function fileBlock(title, code) {
    const escaped = escapeHtml(code);
    const codeAttr = code.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/\n/g, "&#10;");
    return `<div class="file-block">
      <div class="file-block-header">
        <span>${escapeHtml(title)}</span>
        <button class="copy-btn" data-code="${codeAttr}">Copiar</button>
      </div>
      <pre>${escaped}</pre>
    </div>`;
  }

  function renderError(error, source) {
    const lines = source.split("\n");
    const line = error.line;
    let snippet = "";
    if (line && line >= 1 && line <= lines.length) {
      snippet = `<div style="margin-top:6px; color:#ddd;">Línea ${line}: <code style="background:#000;padding:2px 5px;border-radius:3px;">${escapeHtml(lines[line - 1].trim())}</code></div>`;
    }
    output.innerHTML = `<div class="msg-error">
      <div class="msg-title">✗ Error de compilación [${escapeHtml(error.code)}]</div>
      <div>${escapeHtml(error.message)}</div>
      ${snippet}
    </div>`;
    setStatus(`✗ ${error.code}` + (line ? ` — línea ${line}` : ""), "error");
  }

  function setStatus(text, kind) {
    statusbar.textContent = text;
    statusbar.className = "statusbar" + (kind === "error" ? " has-error" : kind === "warning" ? " has-warning" : "");
  }

  // ---------------- Botones ----------------

  btnCompile.addEventListener("click", compile);

  btnDownload.addEventListener("click", async () => {
    const source = codeArea.value;
    if (!source.trim()) return;

    btnDownload.disabled = true;
    const originalText = btnDownload.textContent;
    btnDownload.textContent = "Generando .zip…";

    try {
      const response = await fetch("/download-zip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source,
          preserve_comments: chkPreserveComments.checked,
        }),
      });

      const contentType = response.headers.get("Content-Type") || "";
      if (contentType.includes("application/json")) {
        // El servidor detecto un error de compilacion y devolvio JSON en vez de zip
        const data = await response.json();
        renderError(data.error, source);
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "entityscript_output.zip";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setStatus("✗ No se pudo generar el .zip — revisá la conexión con el servidor", "error");
    } finally {
      btnDownload.textContent = originalText;
      btnDownload.disabled = false;
    }
  });

  let exampleMenuOpen = false;
  btnExample.addEventListener("click", (e) => {
    e.stopPropagation();
    if (exampleMenuOpen) return;
    exampleMenuOpen = true;

    const menu = document.createElement("div");
    menu.style.cssText = "position:fixed; background:#2d2d2d; border:1px solid #3c3c3c; border-radius:6px; padding:4px; z-index:999; box-shadow:0 4px 20px rgba(0,0,0,0.4);";
    const rect = btnExample.getBoundingClientRect();
    menu.style.top = rect.bottom + 4 + "px";
    menu.style.left = rect.left + "px";

    for (const [label, code] of Object.entries(EXAMPLES)) {
      const item = document.createElement("div");
      item.textContent = label;
      item.style.cssText = "padding:7px 14px; font-size:13px; cursor:pointer; border-radius:4px; white-space:nowrap;";
      item.addEventListener("mouseenter", () => (item.style.background = "#3c3c3c"));
      item.addEventListener("mouseleave", () => (item.style.background = "transparent"));
      item.addEventListener("click", () => {
        codeArea.value = code;
        codeArea.dispatchEvent(new Event("input"));
        compile();
        document.body.removeChild(menu);
        exampleMenuOpen = false;
      });
      menu.appendChild(item);
    }
    document.body.appendChild(menu);

    const closeMenu = () => {
      if (menu.parentElement) document.body.removeChild(menu);
      exampleMenuOpen = false;
      document.removeEventListener("click", closeMenu);
    };
    setTimeout(() => document.addEventListener("click", closeMenu), 0);
  });

  chkPreserveComments.addEventListener("change", () => { if (chkAutoCompile.checked) compile(); });

  // ---------------- Autosave ----------------
  // Guarda el codigo en disco (via /save) cada vez que el usuario deja de
  // escribir por un momento, para no perder el trabajo si cierra la
  // pestaña sin querer. Se reutiliza el mismo debounce que ya dispara la
  // autocompilacion, para no duplicar timers.

  let saveTimer = null;

  function scheduleAutosave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      try {
        await fetch("/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source: codeArea.value }),
        });
      } catch (err) {
        // El autosave es silencioso: si falla, no interrumpe al usuario.
        // El peor caso es perder el ultimo autosave, no el trabajo en curso.
      }
    }, 800);
  }

  codeArea.addEventListener("input", scheduleAutosave);

  // ---------------- Inicio ----------------
  // Intenta cargar el ultimo autosave; si no hay nada guardado (primera
  // vez que se usa el editor, o se borro .autosave.es), cae al ejemplo
  // basico de Coin.

  async function loadInitialCode() {
    try {
      const response = await fetch("/load");
      const data = await response.json();
      if (data.ok && data.source && data.source.trim()) {
        return data.source;
      }
    } catch (err) {
      // Sin conexion al servidor todavia (raro, recien arranco) -- se
      // sigue con el ejemplo por defecto sin interrumpir al usuario.
    }
    return EXAMPLES["01 - Coin (básico)"];
  }

  (async () => {
    codeArea.value = await loadInitialCode();
    updateLineNumbers();
    charCount.textContent = codeArea.value.length + " caracteres";
    compile();
  })();
})();
