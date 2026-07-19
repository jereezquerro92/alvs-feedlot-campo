# Scene bank

Closed set of terminal frames. The workflow SELECTS one frame by state
name and fills its `{slots}`; nothing here is generated at runtime. Each
frame is plain ASCII plus cast emoji only, max 64 columns wide, printed
as-is (the caller applies color, never structure).

Cast: hunter 🎯, falcon 🦅, hound 🐕 (forest); tavernkeeper 🍺 (tavern, an
`if`); mage 🧙 (tavern) with its own familiars — owl 🦉, cat 🐈‍⬛, hound 🐕,
mouse 🐁; warrior ⚔️ and archer 🏹 (camp, parallel builders); priest 🙏
(camp gate); shadow 👤 (stalking); bard 🎻 (plaza).

Two of these are script, not agents: the tavernkeeper is an `if` on the
hunter's domain, and the task is pure assembly. They still get a frame —
a render does not care whether the thing it renders is a model or an `if`.

The warrior and the archer are two separate builders, not one character
under two names — each gets its own frame, printed independently. The
archer's frame is simply never selected on a backend-only issue, the same
way the warrior's is never selected on a frontend-only one.

Format per frame: a two-line title bar naming the state and the issue,
a small restrained figure, the slot data, one quoted line of character
speech in Spanish rioplatense.

---

## hunter-start

slots: `issue_number`, `issue_title`, `prey_tag`

```
+----------------------------------------------------------+
 🎯 HUNTER-START            issue #{issue_number}
+----------------------------------------------------------+

   .-""-.
  ( 🎯   )
   '-..-'

 presa: {prey_tag}
 "{issue_title}"

 hunter: "A ver que bicho tenemos hoy..."

+----------------------------------------------------------+
```

---

## falcon-clean

slots: `issue_number`, `scanned_count`

```
+----------------------------------------------------------+
 🦅 FALCON-CLEAN            issue #{issue_number}
+----------------------------------------------------------+

        🦅
      ~~~~~~~

 rastreados: {scanned_count} issues/PRs
 sin gemelos, sin fantasmas.

 falcon: "Cielo despejado, jefe. No hay mellizos."

+----------------------------------------------------------+
```

---

## falcon-finding

slots: `issue_number`, `found_number`, `found_type`, `found_title`

```
+----------------------------------------------------------+
 🦅 FALCON-FINDING          issue #{issue_number}
+----------------------------------------------------------+

        🦅
      ~~~~~~~
        v

 {found_type} #{found_number}
 "{found_title}"

 falcon: "Epa. Esto ya lo cace antes."

+----------------------------------------------------------+
```

---

## falcon-emergency

slots: `issue_number`, `found_number`, `found_type`, `found_title`

```
+----------------------------------------------------------+
 🦅 FALCON-EMERGENCY   !!   issue #{issue_number}
+----------------------------------------------------------+

        🦅
      =======
       !!!!!

 {found_type} #{found_number}
 "{found_title}"

 falcon: "Alerta. Esto esta que arde, che."

+----------------------------------------------------------+
```

---

## hound-trail

slots: `issue_number`, `file_count`, `top_file`

```
+----------------------------------------------------------+
 🐕 HOUND-TRAIL             issue #{issue_number}
+----------------------------------------------------------+

     🐕  . . . .

 rastro en {file_count} archivo(s)
 el mas caliente: {top_file}

 hound: "Aca piso fuerte, seguile el rastro."

+----------------------------------------------------------+
```

---

## constitution-verdict

slots: `issue_number`, `verdict`, `rule_ref`

```
+----------------------------------------------------------+
 🎯 CONSTITUTION-VERDICT    issue #{issue_number}
+----------------------------------------------------------+

      [=====]
      [ LEY ]     🎯
      [=====]

 veredicto: {verdict}
 articulo: {rule_ref}

 hunter: "La ley del pago manda, che."

+----------------------------------------------------------+
```

---

## board-post

slots: `issue_number`, `board_name`, `summary`

```
+----------------------------------------------------------+
 🎯 BOARD-POST              issue #{issue_number}
+----------------------------------------------------------+

      +-----+
      |  X  |    🎯
      +-----+

 tablon: {board_name}
 aviso: "{summary}"

 hunter: "Clavado en el tablero, para que se sepa."

+----------------------------------------------------------+
```

---

## tavernkeeper-briefs

slots: `issue_number`, `domain`

The tavernkeeper no longer picks a hero out of a roster — there is one
mage, always. What it still does is hand over the domain brief.

```
+----------------------------------------------------------+
 🍺 TAVERNKEEPER-BRIEFS     issue #{issue_number}
+----------------------------------------------------------+

      ___🍺___
     [        ]

 dominio: {domain}

 tavernkeeper: "Para esto, che, buscate al mago."

+----------------------------------------------------------+
```

---

## mage-plans

slots: `issue_number`, `familiars_consulted`, `backend_files`, `frontend_files`

`familiars_consulted` renders each familiar sent, or "ninguno" when the
mage planned alone. A familiar that timed out under the 10-minute
watchdog renders as "{name} (perdido)", never silently omitted.

```
+----------------------------------------------------------+
 🧙 MAGE-PLANS              issue #{issue_number}
+----------------------------------------------------------+

        🧙
       /|\
       / \

 familiares: {familiars_consulted}
 backend: {backend_files}   frontend: {frontend_files}

 mage: "Las runas me diran el camino."

+----------------------------------------------------------+
```

---

## warrior-builds

slots: `issue_number`, `files_changed`, `lines_changed`

```
+----------------------------------------------------------+
 ⚔️  WARRIOR-BUILDS          issue #{issue_number}
+----------------------------------------------------------+

        ⚔️
       /|\
       / \

 archivos: {files_changed}   lineas: {lines_changed}

 warrior: "El backend es mio."

+----------------------------------------------------------+
```

---

## archer-builds

slots: `issue_number`, `files_changed`, `lines_changed`

```
+----------------------------------------------------------+
 🏹 ARCHER-BUILDS           issue #{issue_number}
+----------------------------------------------------------+

        🏹
       /|\
       / \

 archivos: {files_changed}   lineas: {lines_changed}

 archer: "Yo cubro el frente."

+----------------------------------------------------------+
```

---

## priest-clean

slots: `issue_number`

```
+----------------------------------------------------------+
 🙏 PRIEST-CLEAN            issue #{issue_number}
+----------------------------------------------------------+

        🙏
       ---

 veredicto: limpio

 priest: "Que nada impuro pase."

+----------------------------------------------------------+
```

---

## priest-blocked

slots: `issue_number`, `finding_count`

Terminal, like falcon-emergency and vampire-refused: the run ends here,
nothing reaches stalking. `finding_count` is a number — the frame never
carries the secret value itself, only that findings exist.

```
+----------------------------------------------------------+
 🙏 PRIEST-BLOCKED     !!   issue #{issue_number}
+----------------------------------------------------------+

        🙏
       !!!!!

 hallazgos: {finding_count}

 priest: "¡Alto! Esto no debe ver la luz."

+----------------------------------------------------------+
```

---

## shadow-reviews

slots: `issue_number`, `verdict`, `finding_count`

```
+----------------------------------------------------------+
 👤 SHADOW-REVIEWS          issue #{issue_number}
+----------------------------------------------------------+

       . 👤 .
       -/ \-

 veredicto: {verdict}
 hallazgos: {finding_count}

 shadow: "No miro curriculum, miro el codigo."

+----------------------------------------------------------+
```

---

## bard-happy

slots: `issue_number`, `pr_number`, `pr_title`

```
+----------------------------------------------------------+
 🎻 BARD-HAPPY              issue #{issue_number}
+----------------------------------------------------------+

        🎻
       ~^~

 PR #{pr_number}
 "{pr_title}"

 bard: "Y asi, la fiera cayo. Cantemos."

+----------------------------------------------------------+
```

---

## bard-sad

slots: `issue_number`, `where_written`, `finding_count`

`where_written` renders the bard's action: "comentario en #{issue_number}"
for the default failed hunt, or "issue #{n}" when the finding was a
genuinely different subject.

```
+----------------------------------------------------------+
 🎻 BARD-SAD                issue #{issue_number}
+----------------------------------------------------------+

        🎻
       -.-

 mapa escrito: {where_written}
 hallazgos reales: {finding_count}

 bard: "No la cazamos, pero volvemos con el mapa."

+----------------------------------------------------------+
```

---

## vampire-refused

slots: `issue_number`, `prey_tag`, `attempt_count`

```
+----------------------------------------------------------+
 🎯 VAMPIRE-REFUSED         issue #{issue_number}
+----------------------------------------------------------+

      _/\_
     ( x  x )    🎯
      \  ~  /

 presa: {prey_tag}
 intentos: {attempt_count}

 vampiro: "Ja. Yo no me quedo muerto."

+----------------------------------------------------------+
```
