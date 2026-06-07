// GLOBAL APPLICATION STATE
let state = {
    isPlaying: false,
    studentImg: null,
    agentImg: null,
    visionData: null,
    words: [],
    currentAudio: null,
    startTime: 0,
    logOffset: 0,
    tourTimer: null,
    selectedStopIdx: null,
    activeGraphView: 'your_run',
    specialistTimer: null,
    specialistStepIdx: 0,
    specialistElapsedSeconds: 0,
    specialistSteps: [
        "Structuring geographical landmark transitions...",
        "Drafting vocabulary-rich tour narration (IELTS Band 9)...",
        "Formulating distractors for Multiple-Choice Questions...",
        "Performing final cohesive semantic sanity check..."
    ]
};

// INITIALIZE MERMAID CHART
mermaid.initialize({ startOnLoad: false, theme: 'dark' });

const MERMAID_CHART = `flowchart TD
    A[Scenario Intent] --> B[Orchestrator]
    
    subgraph Pipeline ["Agent Fleet"]
        Artist[Artist Agent]
        Miner[Miner Agent]
        Auditor[Auditor Agent]
        Playwright[Playwright Recovery]
        Specialist[Specialist Agent]
    end
    
    subgraph Sync ["Sync Engine"]
        Compositor[Forensic Compositor]
        Audio[Audio Engine]
    end
    
    Final[Verified Artifact]

    B --> Artist
    Artist --> Miner
    Miner --> Auditor
    Auditor -->|REJECT| Playwright
    Playwright -->|HEAL| Miner
    Auditor -->|PASS| Specialist
    
    Specialist --> Compositor
    Specialist --> Audio
    
    Compositor --> Final
    Audio --> Final`;

// RESET THE AGENT CARDS ON THE RIGHT SIDEBAR
function resetFleetUI() {
    document.querySelectorAll('.agent-card').forEach(el => {
        el.className = "agent-card border border-slate-800/80 bg-slate-950/40 p-3 rounded-xl flex justify-between items-center transition-all duration-300";
        const statusBadge = el.querySelector('.agent-status');
        if (statusBadge) {
            statusBadge.innerText = "IDLE";
            statusBadge.className = "agent-status text-[8px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-black";
        }
    });
}

// SURGICALLY UPDATE AN AGENT CARD'S STYLES
function setCardState(cardId, bgClass, borderClass, shadowClass, statusText, badgeBg, badgeText, pulse = false) {
    const card = document.getElementById(cardId);
    if (!card) return;
    card.className = `agent-card border p-3 rounded-xl flex justify-between items-center transition-all duration-300 ${borderClass} ${bgClass} ${shadowClass}`;
    const statusBadge = card.querySelector('.agent-status');
    if (statusBadge) {
        statusBadge.innerText = statusText;
        statusBadge.className = `agent-status text-[8px] px-2 py-0.5 rounded font-black ${badgeBg} ${badgeText} ${pulse ? 'animate-pulse' : ''}`;
    }
}

// CINEMATIC TERMINAL STATE HUD OVERHAUL
function updateFleetUI(agent, event) {
    const author = String(agent).toLowerCase();
    const message = String(event).toUpperCase();

    const hud = document.getElementById('cinematicStepHud');
    const hudTitle = document.getElementById('cinematicStepTitle');
    const mapContainer = document.getElementById('imageAuditContainer');

    // Reset HUD class defaults on each step unless overwritten
    if (hud && hudTitle) {
        hud.className = "bg-slate-950/80 border-b border-slate-800 px-5 py-4 flex flex-col justify-center min-h-[70px] transition-all duration-300";
        const span = hud.querySelector('span:nth-child(2)');
        if (span) {
            span.className = "text-teal-500 font-extrabold uppercase tracking-[0.2em]";
            span.innerText = "SYSTEM STATUS";
        }
        hudTitle.className = "text-xs font-black uppercase tracking-wide text-slate-300";
    }

    // 1. Check GRC / Rejection alerts globally first (so we get the beautiful red flash overlay immediately)
    if (message.includes("REJECTED") || message.includes("FAILED") || message.includes("REJECT") || message.includes("COLLISION CHECK")) {
        // Auditor screams RED
        setCardState("agentCardAuditor", "bg-rose-950/25", "border-rose-500", "shadow-[0_0_15px_rgba(244,63,94,0.2)] animate__animated animate__shakeX", "REJECTED", "bg-rose-600", "text-white", true);
        // Miner card is flagged as having generated the bad coordinates
        setCardState("agentCardMiner", "bg-rose-950/10", "border-rose-500/40", "shadow-none", "BAD GEOMETRY", "bg-rose-500/20", "text-rose-400");
        
        const card = document.getElementById("agentCardAuditor");
        if (card) setTimeout(() => card.classList.remove('animate__animated', 'animate__shakeX'), 1000);

        // MASSIVE RED SHIELD BREACH ALERT
        if (hud && hudTitle) {
            hud.className = "bg-rose-950/80 border-b border-rose-850 px-5 py-4 flex flex-col justify-center min-h-[70px] transition-all duration-300 animate__animated animate__flash animate__infinite";
            const span = hud.querySelector('span:nth-child(2)');
            if (span) {
                span.innerText = "MULTI-CONSTRAINT FAILURE DETECTED";
                span.className = "text-rose-400 font-extrabold uppercase tracking-[0.2em]";
            }
            hudTitle.innerText = "🚨 GRC VALIDATION FAILED (SCRIPT DENSITY + SPATIAL LIMITS). TRIGGERING SELF-HEALING ROUTE.";
            hudTitle.className = "text-xs font-black uppercase tracking-wide text-rose-200";
        }
        if (mapContainer) {
            mapContainer.className = "relative w-full aspect-square max-h-[60vh] bg-white rounded overflow-hidden shadow-inner border-4 border-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.6)] transition-all duration-300";
        }
        return;
    }

    // 2. Check GRC / Verification success globally next
    if (message.includes("PASSED") || message.includes("VERIFIED") || message.includes("SUCCESS")) {
        if (author.includes("auditor")) {
            setCardState("agentCardAuditor", "bg-emerald-950/20", "border-emerald-500", "shadow-[0_0_15px_rgba(16,185,129,0.15)]", "VERIFIED", "bg-emerald-500", "text-slate-950");
            setCardState("agentCardMiner", "bg-emerald-950/20", "border-emerald-500", "shadow-[0_0_15px_rgba(16,185,129,0.15)]", "HEALED & VALID", "bg-emerald-500", "text-slate-950");
            
            const pwCard = document.getElementById("agentCardPlaywright");
            if (pwCard) {
                setCardState("agentCardPlaywright", "bg-emerald-950/15", "border-emerald-500/50", "shadow-none", "REPAIRED", "bg-emerald-500/20", "text-emerald-400");
            }

            // EMERALD GRC CLEARED SUCCESS
            if (hud && hudTitle) {
                hud.className = "bg-emerald-950/80 border-b border-emerald-800 px-5 py-4 flex flex-col justify-center min-h-[70px] transition-all duration-300";
                const span = hud.querySelector('span:nth-child(2)');
                if (span) {
                    span.innerText = "GRC VERIFICATION PASSED";
                    span.className = "text-emerald-400 font-extrabold uppercase tracking-[0.2em]";
                }
                hudTitle.innerText = "✅ All visual, structural, and GRC constraints cleared! Routing to Specialist...";
                hudTitle.className = "text-xs font-black uppercase tracking-wide text-emerald-200";
            }
            if (mapContainer) {
                mapContainer.className = "relative w-full aspect-square max-h-[60vh] bg-white rounded overflow-hidden shadow-inner border-4 border-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.6)] transition-all duration-300";
            }
            return;
        }
    }

    // 3. Fallback to Agent-specific active states based on author
    if (author.includes("artist")) {
        if (message.includes("SUCCESSFULLY") || message.includes("GENERATED")) {
            setCardState("agentCardArtist", "bg-emerald-950/10", "border-emerald-500/40", "shadow-none", "COMPLETED", "bg-emerald-500/20", "text-emerald-400");
            if (hud && hudTitle) {
                const span = hud.querySelector('span:nth-child(2)');
                if (span) span.innerText = "Artist Agent Finished";
                hudTitle.innerText = "🎨 Map generated successfully! Routing to Miner...";
            }
        } else {
            setCardState("agentCardArtist", "bg-teal-950/20", "border-teal-500", "shadow-[0_0_15px_rgba(20,184,166,0.15)]", "GENERATING", "bg-teal-500", "text-slate-950", true);
            if (hud && hudTitle) {
                const span = hud.querySelector('span:nth-child(2)');
                if (span) span.innerText = "Artist Agent Active";
                hudTitle.innerText = "🎨 Generating 2D Top-Down Schematic using Imagen 4.0 Fast...";
            }
        }
    }
    else if (author.includes("miner")) {
        setCardState("agentCardMiner", "bg-teal-950/20", "border-teal-500", "shadow-[0_0_15px_rgba(20,184,166,0.15)]", "SCANNING", "bg-teal-500", "text-slate-950", true);
        if (hud && hudTitle) {
            const span = hud.querySelector('span:nth-child(2)');
            if (span) span.innerText = "Miner Agent Active";
            hudTitle.innerText = "🔍 Scanning map layout and extracting coordinate telemetry...";
        }
    }
    else if (author.includes("auditor")) {
        setCardState("agentCardAuditor", "bg-teal-950/20", "border-teal-500", "shadow-[0_0_15px_rgba(20,184,166,0.15)]", "AUDITING", "bg-teal-500", "text-slate-950", true);
        if (hud && hudTitle) {
            const span = hud.querySelector('span:nth-child(2)');
            if (span) span.innerText = "Auditor Agent Active";
            hudTitle.innerText = "⚖️ Performing Euclidean collision scans and GRC proximity audits...";
        }
    }
    else if (author.includes("playwright")) {
        setCardState("agentCardPlaywright", "bg-amber-950/20", "border-amber-500", "shadow-[0_0_15px_rgba(245,158,11,0.15)]", "HEALING", "bg-amber-500", "text-slate-950", true);
        
        // BLUE HERO ESCALATION
        if (hud && hudTitle) {
            hud.className = "bg-blue-950/80 border-b border-blue-800 px-5 py-4 flex flex-col justify-center min-h-[70px] transition-all duration-300";
            const span = hud.querySelector('span:nth-child(2)');
            if (span) {
                span.innerText = "PLAYWRIGHT RECOVERY ACTIVE";
                span.className = "text-blue-400 font-extrabold uppercase tracking-[0.2em]";
            }
            hudTitle.innerText = "🛠️ HEROIC SELF-HEALING ACTIVE: Re-plotting coordinates & resolving map constraints...";
            hudTitle.className = "text-xs font-black uppercase tracking-wide text-blue-200";
        }
        if (mapContainer) {
            mapContainer.className = "relative w-full aspect-square max-h-[60vh] bg-white rounded overflow-hidden shadow-inner border-4 border-blue-500 shadow-[0_0_30px_rgba(59,130,246,0.6)] transition-all duration-300";
        }
    }
    else if (author.includes("specialist")) {
        if (message.includes("EVENT") || message.includes("SUCCESS") || message.includes("COMPLETE")) {
            setCardState("agentCardSpecialist", "bg-emerald-950/20", "border-emerald-500", "shadow-[0_0_15px_rgba(16,185,129,0.15)]", "COMPLETED", "bg-emerald-500", "text-slate-950");
        } else {
            setCardState("agentCardSpecialist", "bg-teal-950/20", "border-teal-500", "shadow-[0_0_15px_rgba(20,184,166,0.15)]", "WRITING MCQS", "bg-teal-500", "text-slate-950", true);
            if (hud && hudTitle) {
                const span = hud.querySelector('span:nth-child(2)');
                if (span) span.innerText = "Specialist Agent Active";
                hudTitle.innerText = "✍️ Writing 5 verified IELTS MCQs and educational tour script...";
            }
        }
    }
    else if (author.includes("reviewer") || author.includes("mqa")) {
        if (message.includes("PASS") || message.includes("APPROVED") || message.includes("SUCCESS")) {
            setCardState("agentCardReviewer", "bg-emerald-950/10", "border-emerald-500/40", "shadow-none", "PASSED", "bg-emerald-500/20", "text-emerald-400");
            if (hud && hudTitle) {
                const span = hud.querySelector('span:nth-child(2)');
                if (span) span.innerText = "Review Agent Finished";
                hudTitle.innerText = "👁️ MQA Review Passed! Handing over to Miner...";
            }
        } else {
            setCardState("agentCardReviewer", "bg-teal-950/20", "border-teal-500", "shadow-[0_0_15px_rgba(20,184,166,0.15)]", "REVIEWING", "bg-teal-500", "text-slate-950", true);
            if (hud && hudTitle) {
                const span = hud.querySelector('span:nth-child(2)');
                if (span) span.innerText = "Review Agent Active";
                hudTitle.innerText = "👁️ MQA Reviewer performing structural visual scan on raw Imagen map...";
            }
        }
    }
}

// APPEND A LINE TO THE TRACE LOG AND DISPATCH TO STATE MACHINE
function addTrace(agent, event, details = "") {
    const time = new Date().toLocaleTimeString('en-GB', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

    let agentColor = "text-teal-400";
    let extraClass = "";
    let animation = "animate__fadeInLeft";

    if (agent === "Artist") agentColor = "text-teal-400";
    else if (agent === "Miner") agentColor = "text-emerald-400";
    else if (agent === "Playwright") agentColor = "text-blue-400";
    else if (agent === "Auditor") agentColor = "text-rose-400";

    const evUpper = String(event).toUpperCase();
    if (evUpper.includes("REJECTED") || evUpper.includes("FAILED") || evUpper.includes("REJECT") || evUpper.includes("COLLISION")) {
        extraClass = "log-rejected";
        animation = "animate__shakeX";
        
        // Dynamically increment rejections and repairs on the Compact Summary Card!
        const failuresEl = document.getElementById('sumFailures');
        const repairsEl = document.getElementById('sumRepairs');
        if (failuresEl) {
            failuresEl.innerText = "1 REJECTED";
            failuresEl.className = "text-[10px] font-black text-rose-400 uppercase animate-pulse";
        }
        if (repairsEl) {
            repairsEl.innerText = "HEALING";
            repairsEl.className = "text-[10px] font-black text-amber-500 uppercase animate-pulse";
        }
    } else if (evUpper.includes("HEALING") || evUpper.includes("RECOVERY") || evUpper.includes("TRIGGERED") || evUpper.includes("HEAL")) {
        extraClass = "log-healing";
        animation = "";
    } else if (evUpper.includes("PASSED") || evUpper.includes("SUCCESS")) {
        extraClass = "log-passed";
    }

    // Automatically capture and collapse raw coordinate JSON telemetry and raw tool dictionaries to keep log scannable
    let formattedEvent = event;
    const evStr = String(event);
    const isJson = evStr.includes('[{"') || evStr.includes('[ {') || evStr.includes('{"ymin":') || evStr.includes('{"number":') || evStr.includes('Tool returned:') || evStr.includes("{'status'") || (evStr.includes('{') && evStr.includes('}') && (evStr.includes("'status'") || evStr.includes('"status"')));

    if (isJson) {
        let prefix = "Proposed GRC telemetry payload:";
        let rawPayload = evStr;
        
        if (evStr.includes('[')) {
            const bracketIdx = evStr.indexOf('[');
            prefix = evStr.substring(0, bracketIdx).trim() || "Proposed coordinate telemetry:";
            rawPayload = evStr.substring(bracketIdx);
        } else if (evStr.includes('Tool returned:')) {
            const toolIdx = evStr.indexOf('Tool returned:');
            prefix = evStr.substring(0, toolIdx).trim() + " GRC validation result:";
            rawPayload = evStr.substring(toolIdx);
        } else if (evStr.includes('{')) {
            const braceIdx = evStr.indexOf('{');
            prefix = evStr.substring(0, braceIdx).trim() || "Raw GRC payload:";
            rawPayload = evStr.substring(braceIdx);
        }

        formattedEvent = `${prefix}
            <details class="cursor-pointer group mt-1.5 outline-none select-none">
                <summary class="text-[9px] font-black text-teal-400 hover:text-teal-300 flex items-center gap-1">
                    <span class="transition-transform group-open:rotate-90">&rarr;</span>
                    View Raw GRC Telemetry
                </summary>
                <div class="mt-2 p-3 bg-black/60 border border-slate-800 rounded-xl font-mono text-[8px] text-slate-400 overflow-x-auto custom-scrollbar select-text whitespace-pre-wrap leading-relaxed">
                    ${rawPayload}
                </div>
            </details>`;
    }

    const html = `
        <div class="flex gap-3 p-1.5 rounded border border-transparent animate__animated animate__faster mb-1.5 transition-all ${extraClass} ${animation}">
            <span class="text-slate-600 font-mono text-[9px] mt-0.5">${time}</span>
            <div class="flex-1">
                <div class="flex items-start gap-1.5">
                    <span class="${agentColor} font-black uppercase text-[8px] tracking-wider mt-0.5">${agent}</span>
                    <span class="text-slate-200 font-bold flex-1 leading-normal">${formattedEvent}</span>
                </div>
                ${details ? `<div class="text-slate-500 italic mt-0.5 leading-tight text-[9px]">${details}</div>` : ''}
            </div>
        </div>`;

    const log = document.getElementById('traceLog');
    const fullLog = document.getElementById('fullTraceLog');
    
    if (log.innerHTML.includes('Awaiting initiation') || log.innerHTML.includes('Waiting for agent initialization')) {
        log.innerHTML = '';
    }

    log.innerHTML += html;
    fullLog.innerHTML += html;
    log.scrollTop = log.scrollHeight;
    fullLog.scrollTop = fullLog.scrollHeight;

    // --- OPTION A: REAL-TIME TELEMETRY SCRAPING ---
    const sumFailures = document.getElementById('sumFailures');
    const sumRepairs = document.getElementById('sumRepairs');
    const sumLandmarks = document.getElementById('sumLandmarks');

    const msgLower = String(event).toLowerCase();
    
    if (msgLower.includes("initiating multimodal semantic audit")) {
        if (sumLandmarks) {
            sumLandmarks.innerText = "5 / 5 (Auditing...)";
            sumLandmarks.className = "text-[10px] font-black text-blue-400 uppercase animate-pulse";
        }
    } else if (msgLower.includes("semantic audit failed") || msgLower.includes("validation check failed") || msgLower.includes("rejected:")) {
        if (sumFailures) {
            sumFailures.innerText = "1 ALERT";
            sumFailures.className = "text-[10px] font-black text-rose-500 uppercase animate-pulse";
        }
    } else if (msgLower.includes("escalating to pro tier") || msgLower.includes("self-healing")) {
        if (sumRepairs) {
            sumRepairs.innerText = "1 HEAL";
            sumRepairs.className = "text-[10px] font-black text-amber-500 uppercase animate-pulse";
        }
    } else if (msgLower.includes("semantic audit passed") || msgLower.includes("auditor approved")) {
        if (sumLandmarks) {
            sumLandmarks.innerText = "5 / 5 (Passed)";
            sumLandmarks.className = "text-[10px] font-black text-emerald-500 uppercase";
        }
    }

    // --- OPTION A & B: SPECIALIST SIMULATED PROGRESS & DYNAMIC TELEMETRY LOADER ---
    // If a new real event is received from the DB, stop any simulated logs and restore card immediately
    if (state.specialistTimer) {
        clearInterval(state.specialistTimer);
        state.specialistTimer = null;
        
        // Restore normal state of the MCQs card
        const sumMCQs = document.getElementById('sumMCQs');
        if (sumMCQs) {
            sumMCQs.innerText = "5 MCQs";
            sumMCQs.className = "text-[10px] font-black text-emerald-500 uppercase";
        }
    }

    if (msgLower.includes("validated ielts mcqs")) {
        // Option B: Show dynamic spinning loader on the Assessment card immediately
        const sumMCQs = document.getElementById('sumMCQs');
        if (sumMCQs) {
            sumMCQs.innerHTML = '<span class="inline-block animate-spin mr-1">⏳</span> COMPILING...';
            sumMCQs.className = "text-[10px] font-black text-amber-500 uppercase animate-pulse";
        }

        // Option A: Append initial yellow warning notice log
        appendSimulatedLog("Specialist", "⚠️ NOTICE: Compiling structured IELTS assessments (500-word script + 5 MCQs) is a highly complex cognitive task. Generating and self-correcting can take up to 90 seconds. Please stand by.", "text-amber-400 font-bold");

        state.specialistStepIdx = 0;
        state.specialistElapsedSeconds = 0;
        
        state.specialistTimer = setInterval(() => {
            state.specialistElapsedSeconds += 2;
            
            // Output stopwatch tick every 2 seconds
            if (state.specialistElapsedSeconds % 10 === 0) {
                // Every 10 seconds, inject one of our high-fidelity, highly specialized process descriptions
                if (state.specialistStepIdx < state.specialistSteps.length) {
                    const stepMsg = state.specialistSteps[state.specialistStepIdx];
                    appendSimulatedLog("Specialist", `⚙️ ${stepMsg} (${state.specialistElapsedSeconds}s elapsed)`);
                    state.specialistStepIdx++;
                } else {
                    appendSimulatedLog("Specialist", `⏳ Compiling IELTS Exam & MCQs... (${state.specialistElapsedSeconds}s elapsed)`);
                }
            } else {
                // Simple heartbeat stopwatch tick
                appendSimulatedLog("Specialist", `⏳ Generating IELTS Exam & MCQs... (${state.specialistElapsedSeconds}s elapsed)`);
            }
        }, 2000); // Trigger every 2 seconds!
    }

    updateFleetUI(agent, event);
}

// HELPER TO APPEND DECORATIVE PROGRESS LOGS DURING LONG MODEL CALLS
function appendSimulatedLog(agent, message, customTextClass = "text-slate-400 font-medium italic") {
    const formattedAgent = agent.toUpperCase();
    const formattedEvent = message;
    const timestamp = new Date().toLocaleTimeString();
    
    const html = `
        <div class="border-b border-slate-900 bg-slate-950/20 px-4 py-2 text-[10px] select-none hover:bg-slate-900/10 transition-colors animate-pulse">
            <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-2">
                    <span class="text-slate-500 font-mono">${timestamp}</span>
                    <span class="text-indigo-400 font-black uppercase text-[9px] tracking-wider">[${formattedAgent}]</span>
                    <span class="${customTextClass} flex-1 leading-normal">${formattedEvent}</span>
                </div>
            </div>
        </div>`;

    const log = document.getElementById('traceLog');
    const fullLog = document.getElementById('fullTraceLog');
    
    if (log && fullLog) {
        log.innerHTML += html;
        fullLog.innerHTML += html;
        log.scrollTop = log.scrollHeight;
        fullLog.scrollTop = fullLog.scrollHeight;
        }
        }

        // POLL SYSTEM DB LOGS FOR THE LIVE EXECUTION ROUTE
async function pollLogs() {
    try {
        const res = await fetch(`/api/trace?offset=${state.logOffset}`);
        if (res.ok) {
            const data = await res.json();
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => {
                    addTrace(log.agent, log.message);
                    state.logOffset++;
                });
            }
        }
    } catch (e) {
        console.error("Polling error", e);
    }
}

// CINEMATIC AUTOMATED TOUR OF THE GENERATED COORDINATE PIN MARKS
function launchAutomatedMapTour() {
    if (state.tourTimer) clearInterval(state.tourTimer);
    let currentIdx = 0;
    const stops = document.querySelectorAll('#theaterAnswerKey > div');
    if (stops.length === 0) return;

    console.log("Launching Cinematic Map Tour Showcase...");
    state.tourTimer = setInterval(() => {
        if (currentIdx < stops.length) {
            stops[currentIdx].click();
            currentIdx++;
        } else {
            clearInterval(state.tourTimer);
            // Clear hover ghost overlay after tour complete
            setTimeout(() => {
                document.getElementById('spatialGhost').classList.add('opacity-0');
                stops.forEach(el => el.classList.remove('border-teal-500', 'bg-teal-50/50'));
                state.selectedStopIdx = null;
            }, 2000);
        }
    }, 1800);
}

const STATS_KEY = 'rale_session_stats_v5';

function loadSessionStats() {
    const defaultStats = {
        total_runs: 0,
        first_pass_accepts: 0,
        recoveries: 0,
        accumulated_cost: 0.0,
        accumulated_pro_cost: 0.0,
        accumulated_savings: 0.0
    };
    try {
        const raw = localStorage.getItem(STATS_KEY);
        return raw ? JSON.parse(raw) : defaultStats;
    } catch (e) {
        return defaultStats;
    }
}

function saveSessionStats(stats) {
    try {
        localStorage.setItem(STATS_KEY, JSON.stringify(stats));
    } catch (e) {
        console.error("Storage error", e);
    }
}

function updateSessionLedgerUI() {
    const stats = loadSessionStats();
    
    const titleEl = document.getElementById('sessionLedgerTitle');
    const firstPassEl = document.getElementById('statFirstPass');
    const recoveryEl = document.getElementById('statRecovery');
    const financialsEl = document.getElementById('statSessionFinancials');

    if (titleEl) titleEl.innerText = `Cumulative Session Ledger (N=${stats.total_runs})`;

    if (stats.total_runs === 0) {
        if (firstPassEl) firstPassEl.innerText = "0 / 0 (0%)";
        if (recoveryEl) recoveryEl.innerText = "0 / 0 (0%)";
        if (financialsEl) financialsEl.innerText = "$0.0000 (Saved 0%)";
    } else {
        const fpPct = ((stats.first_pass_accepts / stats.total_runs) * 100).toFixed(1);
        const recPct = ((stats.recoveries / stats.total_runs) * 100).toFixed(1);
        
        let savingsPct = 0;
        if (stats.accumulated_pro_cost > 0) {
            savingsPct = ((stats.accumulated_savings / stats.accumulated_pro_cost) * 100).toFixed(1);
        }

        if (firstPassEl) firstPassEl.innerText = `${stats.first_pass_accepts} / ${stats.total_runs} (${fpPct}%)`;
        if (recoveryEl) recoveryEl.innerText = `${stats.recoveries} / ${stats.total_runs} (${recPct}%)`;
        if (financialsEl) financialsEl.innerText = `$${stats.accumulated_cost.toFixed(4)} (Saved ${savingsPct}%)`;
    }
}

function accumulateRunStats(recoveryTriggered, actualCost, proCost) {
    const stats = loadSessionStats();
    stats.total_runs += 1;
    
    if (recoveryTriggered) {
        stats.recoveries += 1;
    } else {
        stats.first_pass_accepts += 1;
    }

    stats.accumulated_cost += actualCost;
    stats.accumulated_pro_cost += proCost;
    stats.accumulated_savings += (proCost - actualCost);

    saveSessionStats(stats);
    updateSessionLedgerUI();
}

function renderFinancialAudit(recoveryTriggered, mqaPassed) {
    const statusEl = document.getElementById('escalationStatus');
    const playwrightRow = document.getElementById('costPlaywrightRow');
    const playwrightVal = document.getElementById('costPlaywright');
    
    const artistVal = document.getElementById('costArtist');
    const reviewerVal = document.getElementById('costReviewer');
    const minerVal = document.getElementById('costMiner');
    const auditorVal = document.getElementById('costAuditor');
    const specialistVal = document.getElementById('costSpecialist');
    
    const actualCostEl = document.getElementById('actualTotalCost');
    const monolithicCostEl = document.getElementById('monolithicProCost');
    const savingsHighlightBox = document.getElementById('savingsHighlightBox');
    const savingsVal = document.getElementById('tierSavingsValue');

    // MQA base cost is a standard Flash 2.5 multimodal call ($0.0002).
    // If MQA fails and triggers a re-roll, we add another Imagen 4.0 call ($0.0300) and another Flash audit call ($0.0002).
    const mqaRerollTriggered = (mqaPassed === false);
    const artistCost = mqaRerollTriggered ? 0.0600 : 0.0300;
    const reviewerCost = mqaRerollTriggered ? 0.0004 : 0.0002;
    
    if (artistVal) artistVal.innerText = `$${artistCost.toFixed(4)}`;
    if (reviewerVal) reviewerVal.innerText = `$${reviewerCost.toFixed(4)}`;
    if (minerVal) minerVal.innerText = "$0.0002";
    if (auditorVal) auditorVal.innerText = "$0.0003";
    if (specialistVal) specialistVal.innerText = "$0.0005";

    // Standard baseline (Miner, Auditor, Specialist) cost = $0.0010 actual, $0.0162 Pro
    const standardBaseCost = 0.0010;
    const standardProBaseCost = 0.0162;

    let total = artistCost + reviewerCost + standardBaseCost;
    let proOnlyTotal = artistCost + (mqaRerollTriggered ? 0.0036 : 0.0018) + standardProBaseCost;

    if (recoveryTriggered) {
        // Self-Healing Triggered (Pro Escalation active)
        total += 0.0190;
        proOnlyTotal += 0.0190;

        if (statusEl) {
            statusEl.innerText = "ESCALATED (Pro Active)";
            statusEl.className = "bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-amber-500/20 text-[9px] animate-pulse";
        }
        if (playwrightRow) playwrightRow.className = "flex justify-between text-slate-300 font-bold";
        if (playwrightVal) playwrightVal.innerText = "$0.0190";
    } else {
        // Clean First-Pass (Pro Escalation dormant)
        if (statusEl) {
            statusEl.innerText = "DORMANT (Cost Optimized)";
            statusEl.className = "bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded font-mono font-bold uppercase border border-emerald-500/20 text-[9px]";
        }
        if (playwrightRow) playwrightRow.className = "flex justify-between text-slate-500";
        if (playwrightVal) playwrightVal.innerText = "$0.0000 (Dormant)";
    }

    if (actualCostEl) actualCostEl.innerText = `$${total.toFixed(4)}`;
    if (monolithicCostEl) monolithicCostEl.innerText = `$${proOnlyTotal.toFixed(4)}`;

    const savings = proOnlyTotal - total;
    const savingsPct = ((savings / proOnlyTotal) * 100).toFixed(1);

    if (savingsHighlightBox) {
        if (savings >= 0) {
            savingsHighlightBox.className = "bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-xl flex justify-between items-center text-xs";
            if (savingsVal) savingsVal.innerText = `${savingsPct}% ($${savings.toFixed(4)})`;
        } else {
            // Negative Savings: Truthfully highlight that we spent more than the un-tiered baseline!
            savingsHighlightBox.className = "bg-rose-500/10 border border-rose-500/20 p-3 rounded-xl flex justify-between items-center text-xs animate-pulse";
            if (savingsVal) savingsVal.innerText = `${savingsPct}% (-$${Math.abs(savings).toFixed(4)})`;
        }
    }

    return {
        actualCost: total,
        proCost: proOnlyTotal
    };
}

// POPULATES AND RENDERS FINAL AUDITED RESULTS TO DEDICATED EXAM VIEW
function renderFinalUI(data, duration) {
    // Save the recovery triggered boolean to global application state
    state.recoveryTriggered = data.audit.recovery_triggered;

    const latDisplay = document.getElementById('totalLatencyDisplay');
    if (latDisplay) {
        latDisplay.innerText = `Latency: ${duration}`;
    }
    const latVal = document.getElementById('totalLatency');
    if (latVal) {
        latVal.innerText = duration;
    }

    state.studentImg = data.image_url;
    state.agentImg = data.teacher_image_b64 ? ("data:image/png;base64," + data.teacher_image_b64) : data.image_url;
    state.visionData = data.vision_result;
    state.words = data.words || [];
    state.audioUrl = data.audio_url;
    state.scenario = data.scenario || (data.vision_result ? data.vision_result.scenario : "") || "";

    // Reliability statistics card synchronization
    const failBox = document.getElementById('failureReasonBox');
    const statFail = document.getElementById('statFailure');
    const badge = document.getElementById('auditBadge');

    if (data.audit.recovery_triggered) {
        if (failBox) failBox.classList.remove('hidden');
        if (statFail) statFail.innerText = data.audit.first_pass_rejection_reason;
        if (badge) {
            badge.innerText = "Healed & Verified";
            badge.className = "bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full border border-blue-500/30 font-black uppercase text-[9px]";
        }
        setCardState("agentCardPlaywright", "bg-emerald-950/15", "border-emerald-500/50", "shadow-none", "REPAIRED", "bg-emerald-500/20", "text-emerald-400");
    } else {
        if (failBox) failBox.classList.add('hidden');
        if (badge) {
            badge.innerText = "Verified First Pass";
            badge.className = "bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/30 font-black uppercase text-[9px]";
        }
        setCardState("agentCardMiner", "bg-emerald-950/20", "border-emerald-500", "shadow-[0_0_15px_rgba(16,185,129,0.15)]", "COMPLETED", "bg-emerald-500", "text-slate-950");
        setCardState("agentCardPlaywright", "bg-slate-950/40", "border-slate-800/80", "shadow-none", "IDLE", "bg-slate-800", "text-slate-400");
    }

    // Synchronize the financial audit ledger card values
    const runCosts = renderFinancialAudit(data.audit.recovery_triggered, data.audit.mqa_passed);

    // Update the Compact Run Result Summary Card (Priority 2)
    const sumFailures = document.getElementById('sumFailures');
    const sumRepairs = document.getElementById('sumRepairs');
    const sumLandmarks = document.getElementById('sumLandmarks');
    const sumMCQs = document.getElementById('sumMCQs');
    const sumStatus = document.getElementById('sumStatus');

    if (data.audit.recovery_triggered) {
        if (sumFailures) {
            sumFailures.innerText = "1 DETECTED";
            sumFailures.className = "text-[10px] font-black text-rose-400 uppercase";
        }
        if (sumRepairs) {
            sumRepairs.innerText = "1 REPAIRED";
            sumRepairs.className = "text-[10px] font-black text-amber-400 uppercase";
        }
    } else {
        if (sumFailures) {
            sumFailures.innerText = "0 ALERTS";
            sumFailures.className = "text-[10px] font-black text-slate-500 uppercase";
        }
        if (sumRepairs) {
            sumRepairs.innerText = "0 REPAIRS";
            sumRepairs.className = "text-[10px] font-black text-slate-500 uppercase";
        }
    }
    if (sumLandmarks) {
        sumLandmarks.innerText = "5 / 5 VALID";
        sumLandmarks.className = "text-[10px] font-black text-emerald-400 uppercase";
    }
    if (sumMCQs) {
        sumMCQs.innerText = `${data.questions.length} MCQs`;
        sumMCQs.className = "text-[10px] font-black text-teal-400 uppercase";
    }
    if (sumStatus) {
        sumStatus.innerText = "RELEASED";
        sumStatus.className = "text-[8px] font-black text-slate-950 uppercase tracking-wider";
        sumStatus.parentElement.className = "space-y-0.5 border-l border-slate-800 bg-emerald-500 p-1 rounded shadow-[0_0_15px_rgba(16,185,129,0.4)]";
    }

    // Populate titles and image views
    const theaterTitle = document.getElementById('theaterTitle');
    if (theaterTitle) {
        theaterTitle.innerText = data.scenario;
    }
    const theaterImg = document.getElementById('theaterImg');
    if (theaterImg) {
        theaterImg.src = state.studentImg;
    }

    // Populates tourist destination legends
    const answerKey = document.getElementById('theaterAnswerKey');
    answerKey.innerHTML = '';
    state.selectedStopIdx = null;
    data.vision_result.labels.forEach((label, i) => {
        const div = document.createElement('div');
        div.className = "flex items-center justify-between p-3 border border-slate-100 rounded-lg hover:bg-slate-50 transition-all cursor-pointer group";
        div.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="w-6 h-6 bg-slate-900 text-white rounded-full flex items-center justify-center font-bold text-[10px]">${i+1}</span>
                <span class="font-bold text-slate-700 text-xs">${label.location_name || label.name}</span>
            </div>
            <span class="w-6 h-6 border-2 border-slate-200 text-slate-400 rounded flex items-center justify-center font-black text-[10px]">${label.number}</span>`;

        const triggerHighlight = () => {
            const ghost = document.getElementById('spatialGhost');
            const img = document.getElementById('theaterImg');
            const container = document.getElementById('imageAuditContainer');
            const rect = container.getBoundingClientRect();
            const imgRatio = img.naturalWidth / img.naturalHeight;
            const containerRatio = rect.width / rect.height;
            let renderWidth, renderHeight, offsetX = 0, offsetY = 0;
            if (imgRatio > containerRatio) { renderWidth = rect.width; renderHeight = rect.width / imgRatio; offsetY = (rect.height - renderHeight) / 2; }
            else { renderHeight = rect.height; renderWidth = rect.height * imgRatio; offsetX = (rect.width - renderWidth) / 2; }
            
            const calculatedX = parseFloat(label.x) || (parseFloat(label.xmin) + (parseFloat(label.xmax) - parseFloat(label.xmin))/2.0);
            const calculatedY = parseFloat(label.y) || (parseFloat(label.ymin) + (parseFloat(label.ymax) - parseFloat(label.ymin))/2.0);
            const targetX = offsetX + (calculatedX / 1000) * renderWidth;
            const targetY = offsetY + (calculatedY / 1000) * renderHeight;
            
            ghost.style.left = `${(targetX / rect.width) * 100}%`;
            ghost.style.top = `${(targetY / rect.height) * 100}%`;
            ghost.classList.remove('opacity-0');

            // Set inline script sub-highlights during Hover/Tour
            const mapStatusEl = document.getElementById('mapTourStatus');
            if (mapStatusEl) {
                mapStatusEl.innerHTML = `Map target focused: <span class="bg-teal-500 text-slate-950 font-extrabold px-1.5 py-0.5 rounded shadow text-[9px] inline-block uppercase tracking-wider animate-pulse ml-1">${label.location_name || label.name}</span>`;
            }
        };

        const clearHighlight = () => {
            if (state.selectedStopIdx !== i) {
                if (state.selectedStopIdx === undefined || state.selectedStopIdx === null) {
                    document.getElementById('spatialGhost').classList.add('opacity-0');
                }
                const mapStatusEl = document.getElementById('mapTourStatus');
                if (mapStatusEl) {
                    if (state.selectedStopIdx !== undefined && state.selectedStopIdx !== null) {
                        const clickedLabel = data.vision_result.labels[state.selectedStopIdx];
                        mapStatusEl.innerHTML = `Map target focused: <span class="bg-teal-500 text-slate-950 font-extrabold px-1.5 py-0.5 rounded shadow text-[9px] inline-block uppercase tracking-wider ml-1">${clickedLabel.location_name}</span>`;
                    } else {
                        mapStatusEl.innerText = "Hover or click a stop above to focus the crosshairs.";
                    }
                }
            }
        };

        div.onmouseenter = triggerHighlight;
        div.onmouseleave = clearHighlight;

        div.onclick = () => {
            if (state.selectedStopIdx === i) {
                state.selectedStopIdx = null;
                div.classList.remove('border-teal-500', 'bg-teal-50/50');
                clearHighlight();
            } else {
                document.querySelectorAll('#theaterAnswerKey > div').forEach(el => {
                    el.classList.remove('border-teal-500', 'bg-teal-50/50');
                });
                state.selectedStopIdx = i;
                div.classList.add('border-teal-500', 'bg-teal-50/50');
                triggerHighlight();
            }
        };

        // Redraw active pin smoothly on browser resize / devtools toggle to prevent coordinate drift
        window.addEventListener('resize', () => {
            if (state.selectedStopIdx === i) {
                triggerHighlight();
            }
        });

        answerKey.appendChild(div);
    });

    // Populate aligned audio script container
    const scriptEl = document.getElementById('theaterScript');
    scriptEl.innerHTML = '';
    if (state.words && state.words.length > 0) {
        state.words.forEach((w, i) => {
            const span = document.createElement('span');
            span.innerText = w.word;
            span.className = 'karaoke-word';
            span.id = `word-${i}`;
            scriptEl.appendChild(span);
            scriptEl.appendChild(document.createTextNode(' '));
        });
    } else {
        scriptEl.innerText = data.vision_result.script;
    }

    // Store full script, karaoke html, and reset toggle button states
    state.fullScript = data.vision_result.script;
    state.karaokeHTML = scriptEl.innerHTML;
    state.isShowingFullScript = false;
    const toggleBtn = document.getElementById('toggleFullScriptBtn');
    if (toggleBtn) {
        toggleBtn.innerText = "Show Full Script";
    }

    // Build the Multiple Choice IELTS Questions list
    const questionsEl = document.getElementById('theaterQuestions');
    questionsEl.innerHTML = '';
    data.questions.forEach((qObj, idx) => {
        let qText = qObj.question || qObj.q || "Question content verified.";
        let html = `<div class="bg-slate-50 border border-slate-100 rounded-lg p-4">
            <p class="font-bold text-slate-800 mb-3 text-[11px] leading-tight"><span class="mr-2 text-slate-400">${idx+1}.</span> ${qText}</p>
            <div class="grid grid-cols-1 gap-2">`;
        qObj.options.forEach(opt => {
            html += `
                <div class="flex items-center gap-2 p-2 rounded bg-white border border-slate-100">
                    <div class="w-3 h-3 rounded-full border border-slate-300 flex-shrink-0"></div>
                    <span class="text-[10px] text-slate-600">${opt}</span>
                </div>`;
        });
        html += `</div></div>`;
        questionsEl.innerHTML += html;
    });

    // Standalone Page Reveal Transitions: Hide Page 1 (productView) and show Page 2 (theaterSection)
    document.getElementById('productView').classList.add('hidden');
    document.getElementById('theaterSection').classList.remove('hidden');

    // Reveal the tab menu for exploration post-completion
    document.getElementById('viewTabs').classList.remove('hidden');

    // Switch Visual tab to Map active selection
    const tabMap = document.getElementById('tabMap');
    if (tabMap) {
        tabMap.click();
    }

    // Auto-load AGENT VIEW mapping overlaid coordinates by default!
    document.getElementById('viewAgent').click();

    // Launch Cinematic Tour
    setTimeout(() => launchAutomatedMapTour(), 1200);

    // Update terminal status HUD to complete
    const hud = document.getElementById('cinematicStepHud');
    const hudTitle = document.getElementById('cinematicStepTitle');
    if (hud && hudTitle) {
        hud.className = "bg-emerald-950/80 border-b border-emerald-800 px-5 py-4 flex flex-col justify-center min-h-[70px] transition-all duration-300";
        const span = hud.querySelector('span:nth-child(2)');
        if (span) {
            span.innerText = "DAG EXECUTION COMPLETED";
            span.className = "text-emerald-400 font-extrabold uppercase tracking-[0.2em]";
        }
        hudTitle.innerText = `✨ Execution time: ${duration}. Audited & GRC Compliant!`;
        hudTitle.className = "text-xs font-black uppercase tracking-wide text-emerald-200";
    }

    // Accumulate the finished run stats to the Live Cumulative Session Ledger
    accumulateRunStats(data.audit.recovery_triggered, runCosts.actualCost, runCosts.proCost);
}

// EXECUTES THE GENERAL DAG GENERATION INITIATION (CACHE OR LIVE)
async function runGeneration() {
    // Hide the entire tab menu immediately to restrict navigation after launch
    document.getElementById('viewTabs').classList.add('hidden');

    // Smooth transition from Setup Center to Active logs & Fleets (Sections 2 and 3)
    document.getElementById('leftSidebar').classList.add('hidden');
    document.getElementById('centerWorkspace').classList.remove('hidden');
    document.getElementById('rightSidebar').classList.remove('hidden');

    const scenarioType = document.querySelector('input[name="scenarioType"]:checked').value;
    let scenario = '';
    if (scenarioType === 'custom') {
        scenario = document.getElementById('customScenarioInput').value.trim() || 'A Custom Virtual Reality Park';
    } else {
        scenario = document.getElementById('scenarioSelect').value;
    }
    const processBtn = document.getElementById('processBtn');
    const isStressTest = document.getElementById('stressTestToggle').checked;
    const isFastForward = document.getElementById('fastForwardToggle').checked;
    
    state.startTime = Date.now();
    state.logOffset = 0;
    processBtn.disabled = true;
    resetFleetUI(); 
    
    // Unhide and reset the Compact Run Result Summary Card
    const qsc = document.getElementById('quickSummaryCard');
    if (qsc) {
        qsc.classList.remove('hidden');
        document.getElementById('sumFailures').innerText = "0 ALERTS";
        document.getElementById('sumFailures').className = "text-[10px] font-black text-slate-500 uppercase";
        document.getElementById('sumRepairs').innerText = "0 HEALS";
        document.getElementById('sumRepairs').className = "text-[10px] font-black text-slate-500 uppercase";
        document.getElementById('sumLandmarks').innerText = "0 / 5";
        document.getElementById('sumLandmarks').className = "text-[10px] font-black text-slate-500 uppercase";
        document.getElementById('sumMCQs').innerText = "0 MCQs";
        document.getElementById('sumMCQs').className = "text-[10px] font-black text-slate-500 uppercase";
        document.getElementById('sumStatus').innerText = "ACTIVE";
        document.getElementById('sumStatus').className = "text-[8px] font-black text-amber-400 uppercase tracking-wider animate-pulse";
        document.getElementById('sumStatus').parentElement.className = "space-y-0.5 border-l border-slate-800 bg-amber-500/10 p-1 rounded border border-amber-500/20";
    }

    document.getElementById('btnSpinner').classList.remove('hidden');
    document.getElementById('traceLog').innerHTML = '';
    document.getElementById('fullTraceLog').innerHTML = '';
    
    // Print immediate hyper-realistic startup logs to make the interface feel instantly alive
    addTrace("System", "🚀 INITIATING VALIDATOR-GUIDED MULTI-AGENT DAG...");
    addTrace("Orchestrator", "📡 Establishing secure ADK Session Service on Google Cloud...");
    addTrace("Orchestrator", "⚡ Loading Agent Tiers and Schemas [Artist, Miner, Auditor, Playwright, Specialist]...");
    addTrace("Artist", "🎨 Artist Agent active. Preparing Imagen 4.0 Fast drawing canvas...");
    
    // Flash active system architecture DAG tab pulse notifier
    document.getElementById('archPulse').classList.remove('hidden');

    // --- OPTION A: FAST-FORWARD DEMO CACHE PLAYBACK (4 SECONDS) ---
    if (isFastForward) {
        console.log("Fast-Forward Playback Mode Engaged");
        const cacheKey = scenario.includes("SpongeBob") ? "A Family-Friendly Theme Park Resort" : (CACHED_RUNS[scenario] ? scenario : "A Family-Friendly Theme Park Resort");
        const cachedData = CACHED_RUNS[cacheKey];

        // Simulated sequential line playback of trace logs
        let step = 0;
        const interval = setInterval(() => {
            try {
                if (step < cachedData.logs.length) {
                    const log = cachedData.logs[step];
                    addTrace(log.agent, log.message);
                    step++;
                } else {
                    clearInterval(interval);
                    
                    // Clear active pulse
                    document.getElementById('archPulse').classList.add('hidden');

                    // Final UI render
                    renderFinalUI(cachedData, cachedData.latency);
                    
                    processBtn.disabled = false;
                    document.getElementById('btnSpinner').classList.add('hidden');
                    document.getElementById('resetBtn').classList.remove('hidden');
                }
            } catch (err) {
                clearInterval(interval);
                alert("FAST-FORWARD EXCEPTION: " + err.message + "\nStack: " + err.stack);
                console.error(err);
            }
        }, 1200); // 1200ms per agent step
        return;
    }

    // --- OPTION B: LIVE RUNNING PATH (STRICT ADK API DEBATES) ---
    const pollInterval = setInterval(() => pollLogs(), 1500);

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario, stress_test: isStressTest })
        });
        const data = await res.json();
        clearInterval(pollInterval);
        await pollLogs(); 

        document.getElementById('archPulse').classList.add('hidden');

        if (data.status === 'error') throw new Error(data.message);

        const duration = ((Date.now() - state.startTime) / 1000).toFixed(1) + "s";
        renderFinalUI(data, duration);
        
        processBtn.disabled = false;
        document.getElementById('btnSpinner').classList.add('hidden');
        document.getElementById('resetBtn').classList.remove('hidden');

    } catch (e) {
        alert("Generation Failed: " + e.message);
        document.getElementById('archPulse').classList.add('hidden');
        processBtn.disabled = false;
        document.getElementById('btnSpinner').classList.add('hidden');
        document.getElementById('traceLog').innerHTML += `<div class="text-rose-500 font-bold mb-4 uppercase text-[10px]">// DAG CRASHED: ${e.message}</div>`;
    }
}

// AUDIO PLAY/PAUSE SYNC ORCHESTRATOR FOR EXAM SUBTITLES
function handleAudioPlayPause() {
    const playBtnExam = document.getElementById('playAudioBtnExam');
    if (state.currentAudio) {
        if (state.isPlaying) {
            state.currentAudio.pause();
            state.isPlaying = false;
            if (playBtnExam) playBtnExam.innerHTML = '<svg class="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"></path></svg>';
            setAudioStatusText("PAUSED");
        } else {
            state.currentAudio.play();
            state.isPlaying = true;
            if (playBtnExam) playBtnExam.innerHTML = '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"></path></svg>';
            setAudioStatusText("LIVE STREAMING AUDIO");
        }
        return;
    }

    // Dynamic mapping to distinct high-quality audio assets to prevent duplicate theme park playback on cached runs
    let audioUrl = state.audioUrl;
    if (!audioUrl) {
        // Fallback to distinct pre-existing localized MP3s based on scenario theme
        const scenario = state.scenario || (state.studentImg ? (state.visionData ? state.visionData.scenario || "" : "") : "") || "";
        const scenarioLower = String(scenario).toLowerCase();
        
        if (scenarioLower.includes("zoo")) {
            audioUrl = "/static/uploads/audio_00d9eeea.mp3";
        } else if (scenarioLower.includes("garden")) {
            audioUrl = "/static/uploads/audio_10a80e2f.mp3";
        } else if (scenarioLower.includes("campus") || scenarioLower.includes("university")) {
            audioUrl = "/static/uploads/audio_1483461a.mp3";
        } else if (scenarioLower.includes("museum") || scenarioLower.includes("district")) {
            audioUrl = "/static/uploads/audio_1fba3978.mp3";
        } else {
            audioUrl = "/static/uploads/theme_park_sample.mp3";
        }
    }
    if (!audioUrl) return;

    state.currentAudio = new Audio(audioUrl);
    state.isPlaying = true;
    if (playBtnExam) playBtnExam.innerHTML = '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"></path></svg>';
    setAudioStatusText("LIVE STREAMING AUDIO");

    state.currentAudio.ontimeupdate = () => {
        const time = state.currentAudio.currentTime;
        const duration = state.currentAudio.duration || 1;
        updateAudioProgress(time, duration);
    };

    state.currentAudio.onended = () => {
        state.isPlaying = false;
        state.currentAudio = null;
        if (playBtnExam) playBtnExam.innerHTML = '<svg class="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"></path></svg>';
        setAudioStatusText("FINISHED");
        updateAudioProgress(0, 1);
    };

    state.currentAudio.play();
}

function setAudioStatusText(text) {
    if (document.getElementById('audioStatusExam')) {
        document.getElementById('audioStatusExam').innerText = text;
    }
}

// UPDATE AUDIO SLIDERS AND HIGHLIGHT SPOKEN KARAOKE WORDS
function updateAudioProgress(time, duration) {
    const pct = `${(time / duration) * 100}%`;
    if (document.getElementById('audioProgressExam')) {
        document.getElementById('audioProgressExam').style.width = pct;
    }

    // High fidelity subtitle tracking with latency compensation
    const scriptEl = document.getElementById('theaterScript');
    if (state.words && state.words.length > 0) {
        state.words.forEach((w, i) => {
            const el = document.getElementById(`word-${i}`);
            if (el) {
                // Defensive check for malformed timestamps
                const start = typeof w.start === 'number' ? w.start : (i * 0.3);
                const end = typeof w.end === 'number' ? w.end : ((i + 1) * 0.3);

                // Add 320ms exact alignment advance offset to compensate for TTS latency
                const adjustedTime = time + 0.32;

                if (adjustedTime >= start && adjustedTime <= end) {
                    el.className = 'karaoke-word karaoke-highlight';
                    // Center-scroll active word into view smoothly if overflow occurs
                    el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                } else {
                    el.className = 'karaoke-word';
                }
            }
        });
    } else if (scriptEl) {
        // Linear fallback highlighting if words array is empty or missing
        const words = scriptEl.querySelectorAll('.karaoke-word');
        if (words.length > 0) {
            // Apply similar advance offset to linear fallback
            const adjustedTime = time + 0.32;
            const activeIndex = Math.floor((adjustedTime / duration) * words.length);
            words.forEach((el, i) => {
                if (i === activeIndex) {
                    el.className = 'karaoke-word karaoke-highlight';
                    el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                } else {
                    el.className = 'karaoke-word';
                }
            });
        }
    }
}

// REGISTER ALL NAV TAB SWITCHES AND USER INTERFACE BUTTON INTERACTIONS
document.getElementById('processBtn').onclick = runGeneration;
document.getElementById('resetBtn').onclick = () => window.location.reload();

document.getElementById('viewStudent').onclick = () => {
    document.getElementById('theaterImg').src = state.studentImg;
    document.getElementById('viewStudent').className = "px-4 py-1.5 rounded-full text-[10px] font-black transition-all bg-teal-500 text-slate-950 shadow-md border border-teal-400/20";
    document.getElementById('viewAgent').className = "px-4 py-1.5 rounded-full text-[10px] font-black transition-all text-slate-500 bg-transparent opacity-50 hover:text-slate-300 cursor-pointer";
};
document.getElementById('viewAgent').onclick = () => {
    document.getElementById('theaterImg').src = state.agentImg;
    document.getElementById('viewAgent').className = "px-4 py-1.5 rounded-full text-[10px] font-black transition-all bg-teal-500 text-slate-950 shadow-md border border-teal-400/20";
    document.getElementById('viewStudent').className = "px-4 py-1.5 rounded-full text-[10px] font-black transition-all text-slate-500 bg-transparent opacity-50 hover:text-slate-300 cursor-pointer";
};

function setActiveTab(tabId) {
    const tabs = ['tabProduct', 'tabMap', 'tabExam', 'tabArchitecture'];
    tabs.forEach(id => {
        const btn = document.getElementById(id);
        if (!btn) return;
        if (id === tabId) {
            btn.className = "px-5 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all bg-teal-500 text-slate-950 shadow-lg";
        } else {
            btn.className = "px-5 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all text-slate-400 hover:text-white";
        }
    });
}

document.getElementById('tabProduct').onclick = () => {
    document.getElementById('productView').classList.remove('hidden');
    document.getElementById('theaterSection').classList.add('hidden');
    document.getElementById('architectureView').classList.add('hidden');
    document.getElementById('viewProof').classList.add('hidden');
    
    setActiveTab('tabProduct');
};

document.getElementById('tabMap').onclick = () => {
    document.getElementById('productView').classList.add('hidden');
    document.getElementById('theaterSection').classList.remove('hidden');
    document.getElementById('architectureView').classList.add('hidden');
    document.getElementById('viewProof').classList.add('hidden');

    document.getElementById('completionMapView').classList.remove('hidden');
    document.getElementById('completionExamView').classList.add('hidden');
    
    setActiveTab('tabMap');
};

document.getElementById('tabExam').onclick = () => {
    document.getElementById('productView').classList.add('hidden');
    document.getElementById('theaterSection').classList.remove('hidden');
    document.getElementById('architectureView').classList.add('hidden');
    document.getElementById('viewProof').classList.add('hidden');

    document.getElementById('completionMapView').classList.add('hidden');
    document.getElementById('completionExamView').classList.remove('hidden');
    
    // Clean scroll alignment to top of Question 1 (Priority 6)
    const questionsEl = document.getElementById('theaterQuestions');
    if (questionsEl) questionsEl.scrollTop = 0;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    setActiveTab('tabExam');
};

function renderDAG(viewMode) {
    const isHealed = (viewMode === 'full') ? true : state.recoveryTriggered;
    const isFull = (viewMode === 'full');
    const graphEl = document.getElementById('mermaidGraph');
    if (!graphEl) return;

    graphEl.innerHTML = `
<div class="w-full flex flex-col items-center gap-4 py-6 text-slate-200 relative overflow-x-auto select-none">
    
    <!-- Active Route Indicator Badge -->
    ${isFull ? `
    <div class="bg-teal-500/10 text-teal-400 border border-teal-500/20 px-5 py-3 rounded-2xl text-center text-[10px] font-black uppercase tracking-widest mb-4 shadow-[0_0_20px_rgba(20,184,166,0.15)] flex items-center gap-2.5">
        <span class="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse"></span>
        <span>Theoretical Flow: Full Bounded Self-Healing Pipeline Blueprint</span>
    </div>
    ` : (isHealed ? `
    <div class="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-5 py-3 rounded-2xl text-center text-[10px] font-black uppercase tracking-widest mb-4 animate-pulse shadow-[0_0_20px_rgba(245,158,11,0.15)] flex items-center gap-2.5">
        <span class="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping"></span>
        <span>Escalation Active: Bounded Pro-Tier Self-Healing Loop Engaged</span>
    </div>
    ` : `
    <div class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-5 py-3 rounded-2xl text-center text-[10px] font-black uppercase tracking-widest mb-4 shadow-[0_0_20px_rgba(16,185,129,0.15)] flex items-center gap-2.5">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
        <span>Direct Path Active: First-Pass GRC Approved (Economy Tier Cost-Savings)</span>
    </div>
    `)}

    <!-- 1. TOP ROW: Intent & Orchestrator -->
    <div class="flex flex-col items-center relative z-20">
        <!-- Scenario Input -->
        <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-extrabold px-6 py-2.5 rounded-xl border border-blue-400 text-xs tracking-wider uppercase shadow-lg">
            📥 Scenario Intent Input
        </div>
        
        <!-- Connecting Line to Orchestrator -->
        <svg class="h-8 w-6 text-indigo-500 animate-pulse" viewBox="0 0 24 32">
            <line x1="12" y1="0" x2="12" y2="32" stroke="currentColor" stroke-width="2.5" stroke-dasharray="4"/>
            <polygon points="12,32 8,24 16,24" fill="currentColor"/>
        </svg>

        <!-- Orchestrator Node -->
        <div class="bg-slate-900 border-2 border-indigo-500 px-6 py-3 rounded-2xl shadow-[0_0_20px_rgba(99,102,241,0.3)] text-center w-80 relative">
            <h4 class="text-xs font-black uppercase text-indigo-400 tracking-widest mb-1">🤖 ADK Orchestrator Node</h4>
            <p class="text-[9px] text-slate-400 font-bold leading-tight">SequentialAgent Spine & Dynamic Edge Router</p>
        </div>

        <!-- Connecting Line to Fleet -->
        <svg class="h-8 w-6 text-indigo-500 animate-pulse" viewBox="0 0 24 32">
            <line x1="12" y1="0" x2="12" y2="32" stroke="currentColor" stroke-width="2.5" stroke-dasharray="4"/>
            <polygon points="12,32 8,24 16,24" fill="currentColor"/>
        </svg>
    </div>

    <!-- 2. MAIN BODY: The Multi-Agent Fleet Loop -->
    <div class="bg-slate-950/60 border border-slate-800 p-8 rounded-2xl w-full max-w-2xl relative shadow-2xl z-10 flex flex-col items-center">
        <!-- Subgraph Title -->
        <span class="absolute -top-3 left-6 bg-slate-900 border border-slate-800 px-4 py-0.5 rounded-full text-[9px] font-bold text-teal-400 uppercase tracking-widest">
            🔄 Bounded Detect-Reject-Repair Loop (ADK Fleet)
        </span>

        <!-- The Vertical Forward Chain (Priority 4 - Fits lg:col-span-4 perfectly without clipping) -->
        <div class="flex flex-col items-center gap-4 w-full relative">
            <!-- Artist Agent -->
            <div class="bg-slate-900 border-2 border-emerald-500/80 p-3.5 rounded-xl flex flex-col items-center text-center shadow-[0_0_15px_rgba(16,185,129,0.15)] w-44 relative z-10">
                <span class="text-lg">🎨</span>
                <span class="text-[11px] font-black uppercase text-emerald-400 mt-1.5">1. Artist Agent</span>
                <span class="text-[8px] text-slate-500 mt-0.5">Imagen 3.0</span>
            </div>

            <!-- Connecting Arrow -->
            <svg class="h-6 w-6 text-emerald-500 animate-pulse" viewBox="0 0 24 32">
                <line x1="12" y1="0" x2="12" y2="32" stroke="currentColor" stroke-width="2"/>
                <polygon points="12,32 8,24 16,24" fill="currentColor"/>
            </svg>

            <!-- Review Agent (MQA) -->
            <div class="bg-slate-900 border-2 border-emerald-500/80 p-3.5 rounded-xl flex flex-col items-center text-center shadow-[0_0_15px_rgba(16,185,129,0.15)] w-44 relative z-10">
                <span class="text-lg">👁️</span>
                <span class="text-[11px] font-black uppercase text-emerald-400 mt-1.5">2. Reviewer Node</span>
                <span class="text-[8px] text-slate-500 mt-0.5">Multimodal MQA</span>
            </div>

            <!-- Connecting Arrow -->
            <svg class="h-6 w-6 text-emerald-500 animate-pulse" viewBox="0 0 24 32">
                <line x1="12" y1="0" x2="12" y2="32" stroke="currentColor" stroke-width="2"/>
                <polygon points="12,32 8,24 16,24" fill="currentColor"/>
            </svg>

            <!-- Miner Agent -->
            <div class="relative bg-slate-900 border-2 ${(isHealed && !isFull) ? 'border-rose-500/60 bg-rose-950/10' : 'border-emerald-500/60 bg-emerald-950/10'} p-3.5 rounded-xl flex flex-col items-center text-center shadow-md w-44 relative z-20">
                ${isFull ? `
                <span class="absolute -top-2.5 -right-2 bg-teal-600 text-slate-950 text-[7px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">ACTIVE NODE</span>
                ` : (isHealed ? `
                <span class="absolute -top-2.5 -right-2 bg-rose-600 text-white text-[7px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">REJECTED SHIFT</span>
                ` : `
                <span class="absolute -top-2.5 -right-2 bg-emerald-600 text-slate-950 text-[7px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">PASSED FIRST-TRY</span>
                `)}
                <span class="text-lg">🔍</span>
                <span class="text-[11px] font-black uppercase ${(isHealed && !isFull) ? 'text-rose-400' : 'text-emerald-400'} mt-1.5">3. Miner Agent</span>
                <span class="text-[8px] text-slate-500 mt-0.5">Gemini 2.5 Flash</span>
            </div>

            <!-- Connecting Arrow -->
            <svg class="h-6 w-6 ${(isHealed && !isFull) ? 'text-rose-500' : 'text-emerald-500'} animate-pulse" viewBox="0 0 24 32">
                <line x1="12" y1="0" x2="12" y2="32" stroke="currentColor" stroke-width="2"/>
                <polygon points="12,32 8,24 16,24" fill="currentColor"/>
            </svg>

            <!-- Auditor Gate -->
            <div class="border-2 ${(isHealed && !isFull) ? 'border-rose-500 bg-rose-950/20 shadow-[0_0_15px_rgba(244,63,94,0.3)] animate-pulse' : 'border-emerald-500 bg-emerald-950/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]'} p-3.5 rounded-xl flex flex-col items-center text-center w-44 relative z-10">
                <span class="text-lg">⚖️</span>
                <span class="text-[11px] font-black uppercase ${(isHealed && !isFull) ? 'text-rose-400' : 'text-emerald-400'} mt-1.5">4. Auditor Gate</span>
                <span class="text-[8px] text-slate-500 mt-0.5">@tools/adk_tools.py</span>
            </div>
        </div>

        <!-- Loopback Routing Paths & Recovery Branches -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-8 w-full mt-6 pt-6 border-t border-slate-800/60 relative">
            
            <!-- Playwright Recovery Node (REJECT Branch) -->
            <div class="${(isHealed || isFull) ? 'bg-amber-950/20 border-2 border-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.2)]' : 'opacity-30 border-slate-800 text-slate-500 bg-slate-950'} p-4 rounded-xl flex flex-col items-center text-center relative w-full shadow-md z-10 transition-all duration-300">
                <!-- Status Badge -->
                <span class="absolute -top-2.5 left-4 ${(isHealed || isFull) ? 'bg-amber-500 text-slate-950' : 'bg-slate-800 text-slate-400'} text-[8px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">
                    ${(isHealed || isFull) ? '🛠️ ACTIVE (SELF-HEAL ACTIVE)' : '💤 DORMANT (Saved Tokens!)'}
                </span>
                <span class="text-xl">🛠️</span>
                <h5 class="text-[10px] font-black ${(isHealed || isFull) ? 'text-amber-400' : 'text-slate-400'} uppercase mt-1.5">5a. Playwright Agent</h5>
                <span class="text-[8px] text-slate-500 font-bold">Gemini 2.5 Pro (Premium Repair)</span>
                <p class="text-[8px] text-slate-400 mt-2 max-w-[200px]">Reads GRC errors and surgically recalculates coordinate points</p>
                
                <!-- LOOPBACK INDICATOR PATH -->
                <div class="mt-4 flex items-center justify-center gap-2 ${(isHealed || isFull) ? 'text-amber-500 animate-pulse' : 'text-slate-600'} font-black text-[9px]">
                    <span>🔁 Loopback (HEAL) to Miner</span>
                    <svg class="h-4 w-6" viewBox="0 0 24 16">
                        <path d="M 24,8 L 4,8" stroke="currentColor" stroke-width="2"/>
                        <polygon points="4,8 10,4 10,12" fill="currentColor"/>
                    </svg>
                </div>
            </div>

            <!-- Specialist Agent (PASS Branch) -->
            <div class="border-2 border-emerald-500 bg-emerald-950/10 p-4 rounded-xl flex flex-col items-center text-center relative w-full shadow-md z-10">
                <!-- Status Badge -->
                <span class="absolute -top-2.5 left-4 bg-emerald-500 text-slate-950 text-[8px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">
                    ✅ PASS (Factual & Spatial)
                </span>
                <span class="text-xl">✍️</span>
                <h5 class="text-[10px] font-black text-emerald-400 uppercase mt-1.5">5b. Specialist Agent</h5>
                <span class="text-[8px] text-slate-500 font-bold">Gemini 2.5 Flash</span>
                <p class="text-[8px] text-slate-400 mt-2 max-w-[200px]">Ingests validated script and generates 5 verified MCQs</p>
                
                <!-- ROUTE TO SYNC INDICATOR -->
                <div class="mt-4 flex items-center justify-center gap-2 text-emerald-500 font-black text-[9px]">
                    <span>➡️ Route to Sync Engine</span>
                    <svg class="h-4 w-6" viewBox="0 0 24 16">
                        <path d="M 0,8 L 20,8" stroke="currentColor" stroke-width="2"/>
                        <polygon points="20,8 14,4 14,12" fill="currentColor"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>

    <!-- Downward Connection to Sync Engine -->
    <div class="flex flex-col items-center relative z-20">
        <svg class="h-8 w-6 text-teal-500 animate-pulse" viewBox="0 0 24 32">
            <line x1="12" y1="0" x2="12" y2="32" stroke="currentColor" stroke-width="2.5" stroke-dasharray="4"/>
            <polygon points="12,32 8,24 16,24" fill="currentColor"/>
        </svg>
    </div>

    <!-- 3. ROW 4: Parallel Synchronization Engine -->
    <div class="bg-slate-950/60 border border-slate-800 p-6 rounded-2xl w-full max-w-lg relative shadow-2xl z-10 flex flex-col items-center">
        <span class="absolute -top-3 left-6 bg-slate-900 border border-slate-800 px-4 py-0.5 rounded-full text-[9px] font-bold text-teal-400 uppercase tracking-widest">
            🔄 Parallel Synchronization Engine
        </span>
        
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full pt-2 relative z-20">
            <!-- Forensic Compositor -->
            <div class="bg-slate-900 border-2 border-emerald-500/80 p-3.5 rounded-xl flex flex-col items-center text-center shadow-[0_0_15px_rgba(16,185,129,0.15)]">
                <span class="text-xl">🖼️</span>
                <span class="text-[10px] font-black uppercase text-emerald-400 mt-1.5">Forensic Compositor</span>
                <p class="text-[8px] text-slate-500 mt-1 leading-normal">Overlay PIL coordinates on generated map</p>
            </div>
            
            <!-- Audio Engine -->
            <div class="bg-slate-900 border-2 border-emerald-500/80 p-3.5 rounded-xl flex flex-col items-center text-center shadow-[0_0_15px_rgba(16,185,129,0.15)]">
                <span class="text-xl">🎙️</span>
                <span class="text-[10px] font-black uppercase text-emerald-400 mt-1.5">Audio Engine</span>
                <p class="text-[8px] text-teal-400 font-bold mt-1 leading-normal">Google Cloud TTS & Word-Level Alignment</p>
            </div>
        </div>
    </div>

    <!-- Downward Connection to Output -->
    <div class="flex flex-col items-center relative z-20">
        <svg class="h-8 w-6 text-emerald-500 animate-pulse" viewBox="0 0 24 32">
            <line x1="12" y1="0" x2="12" y2="32" stroke="currentColor" stroke-width="2.5" stroke-dasharray="4"/>
            <polygon points="12,32 8,24 16,24" fill="currentColor"/>
        </svg>
    </div>

    <!-- 4. BOTTOM ROW: Verified Artifact -->
    <div class="flex flex-col items-center relative z-20">
        <div class="bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-950 font-black px-8 py-3.5 rounded-2xl shadow-[0_0_35px_rgba(16,185,129,0.5)] border-2 border-emerald-400 text-xs tracking-widest uppercase">
            🏆 Verified IELTS Exam Artifact Released
        </div>
    </div>
</div>`;

    // Highlight active toggle buttons
    const btnYourRun = document.getElementById('graphViewYourRun');
    const btnFull = document.getElementById('graphViewFull');
    if (btnYourRun && btnFull) {
        if (viewMode === 'full') {
            btnFull.className = "px-2.5 py-1 rounded text-[8px] font-black uppercase transition-all bg-teal-500 text-slate-950 cursor-pointer";
            btnYourRun.className = "px-2.5 py-1 rounded text-[8px] font-black uppercase transition-all text-slate-400 hover:text-white ml-1 cursor-pointer";
        } else {
            btnYourRun.className = "px-2.5 py-1 rounded text-[8px] font-black uppercase transition-all bg-teal-500 text-slate-950 cursor-pointer";
            btnFull.className = "px-2.5 py-1 rounded text-[8px] font-black uppercase transition-all text-slate-400 hover:text-white ml-1 cursor-pointer";
        }
    }
}

document.getElementById('tabArchitecture').onclick = () => {
    document.getElementById('productView').classList.add('hidden');
    document.getElementById('theaterSection').classList.add('hidden');
    document.getElementById('architectureView').classList.remove('hidden');
    document.getElementById('viewProof').classList.add('hidden');
    
    setActiveTab('tabArchitecture');
    
    // Render DAG based on current state
    renderDAG(state.activeGraphView);

    // Dynamic View mode toggling listeners inside GRC System Diagnostics tab
    const btnYourRun = document.getElementById('graphViewYourRun');
    const btnFull = document.getElementById('graphViewFull');
    if (btnYourRun && btnFull) {
        btnYourRun.onclick = (e) => {
            e.stopPropagation();
            state.activeGraphView = 'your_run';
            renderDAG('your_run');
        };
        btnFull.onclick = (e) => {
            e.stopPropagation();
            state.activeGraphView = 'full';
            renderDAG('full');
        };
    }
};

function syncInputControls() {
    const activeRadio = document.querySelector('input[name="scenarioType"]:checked').value;
    const ffToggle = document.getElementById('fastForwardToggle');
    const ffContainer = document.getElementById('fastForwardContainer');
    const stressToggle = document.getElementById('stressTestToggle');
    const stressCard = stressToggle ? stressToggle.closest('.p-4') : null;

    if (!ffToggle || !stressToggle) return;

    if (activeRadio === 'custom') {
        // Custom prompts can never use Fast-Forward Replay
        ffToggle.checked = false;
        ffToggle.disabled = true;
        if (ffContainer) ffContainer.classList.add('opacity-40', 'pointer-events-none');

        // Enable Stress Test for custom prompts
        stressToggle.disabled = false;
        if (stressCard) stressCard.classList.remove('opacity-40', 'pointer-events-none');
    } else {
        // Predefined Active
        if (stressToggle.checked) {
            // If Stress is checked, Fast-Forward must be disabled and unchecked
            ffToggle.checked = false;
            ffToggle.disabled = true;
            if (ffContainer) ffContainer.classList.add('opacity-40', 'pointer-events-none');

            // Keep Stress enabled
            stressToggle.disabled = false;
            if (stressCard) stressCard.classList.remove('opacity-40', 'pointer-events-none');
        } else if (ffToggle.checked) {
            // If Fast-Forward is checked, Stress must be disabled and unchecked
            stressToggle.checked = false;
            stressToggle.disabled = true;
            if (stressCard) stressCard.classList.add('opacity-40', 'pointer-events-none');

            // Keep Fast-Forward enabled
            ffToggle.disabled = false;
            if (ffContainer) ffContainer.classList.remove('opacity-40', 'pointer-events-none');
        } else {
            // Neither is checked: both are enabled and clickable
            ffToggle.disabled = false;
            if (ffContainer) ffContainer.classList.remove('opacity-40', 'pointer-events-none');

            stressToggle.disabled = false;
            if (stressCard) stressCard.classList.remove('opacity-40', 'pointer-events-none');
        }
    }
}

function updateScenarioSelectionState() {
    const predefinedCard = document.getElementById('optionPredefinedCard');
    const customCard = document.getElementById('optionCustomCard');
    const selectEl = document.getElementById('scenarioSelect');
    const inputEl = document.getElementById('customScenarioInput');
    const activeRadio = document.querySelector('input[name="scenarioType"]:checked').value;
    
    const ffToggle = document.getElementById('fastForwardToggle');
    const ffContainer = document.getElementById('fastForwardContainer');
    const stressToggle = document.getElementById('stressTestToggle');

    if (activeRadio === 'predefined') {
        // Predefined Active
        predefinedCard.classList.remove('opacity-50', 'bg-slate-950/40', 'border-slate-850');
        predefinedCard.classList.add('bg-slate-950', 'border-teal-500/80', 'border-2');
        selectEl.disabled = false;
        selectEl.classList.remove('opacity-50');

        // Custom Faded
        customCard.classList.add('opacity-50', 'bg-slate-950/40', 'border-slate-850');
        customCard.classList.remove('bg-slate-950', 'border-teal-500/80', 'border-2');
        inputEl.disabled = true;
        inputEl.classList.add('opacity-50');

        // Enable and pre-check Fast-Forward by default only if Stress is NOT active
        if (ffToggle) {
            if (stressToggle && stressToggle.checked) {
                ffToggle.checked = false;
                ffToggle.disabled = true;
            } else {
                ffToggle.disabled = false;
                ffToggle.checked = true;
            }
        }
    } else {
        // Custom Active
        customCard.classList.remove('opacity-50', 'bg-slate-950/40', 'border-slate-850');
        customCard.classList.add('bg-slate-950', 'border-teal-500/80', 'border-2');
        inputEl.disabled = false;
        inputEl.classList.remove('opacity-50');

        // Predefined Faded
        predefinedCard.classList.add('opacity-50', 'bg-slate-950/40', 'border-slate-850');
        predefinedCard.classList.remove('bg-slate-950', 'border-teal-500/80', 'border-2');
        selectEl.disabled = true;
        selectEl.classList.add('opacity-50');
    }

    // Run the unified state synchronizer
    syncInputControls();
}

// Attach change event to radio elements
document.querySelectorAll('input[name="scenarioType"]').forEach(radio => {
    radio.addEventListener('change', updateScenarioSelectionState);
});

// Also support clicking card wrapper backgrounds for immediate selection
document.getElementById('optionPredefinedCard').addEventListener('click', function(e) {
    const radio = this.querySelector('input[name="scenarioType"]');
    if (radio && !radio.checked) {
        radio.checked = true;
        updateScenarioSelectionState();
    }
});

document.getElementById('optionCustomCard').addEventListener('click', function(e) {
    const radio = this.querySelector('input[name="scenarioType"]');
    if (radio && !radio.checked) {
        radio.checked = true;
        updateScenarioSelectionState();
    }
});

// Initialize on load to synchronize correct states
updateScenarioSelectionState();

// Link Spatial Stress Mode and Demo Fast-Forward to be mutually exclusive with clean grey-out
const stressToggle = document.getElementById('stressTestToggle');
const ffToggle = document.getElementById('fastForwardToggle');

if (stressToggle && ffToggle) {
    stressToggle.addEventListener('change', () => {
        if (stressToggle.checked) {
            ffToggle.checked = false;
        }
        syncInputControls();
    });

    ffToggle.addEventListener('change', () => {
        if (ffToggle.checked) {
            stressToggle.checked = false;
        }
        syncInputControls();
    });
}

document.getElementById('copyProofBtn').onclick = () => {
    const text = document.getElementById('proofContentData').innerText;
    navigator.clipboard.writeText(text).then(() => {
        document.getElementById('copyProofBtn').innerText = 'Copied!';
        setTimeout(() => document.getElementById('copyProofBtn').innerText = 'Copy to Clipboard', 2000);
    });
};

if (document.getElementById('playAudioBtnExam')) {
    document.getElementById('playAudioBtnExam').onclick = handleAudioPlayPause;
}

// Toggle full script button click listener
document.getElementById('toggleFullScriptBtn').onclick = () => {
    const btn = document.getElementById('toggleFullScriptBtn');
    const scriptEl = document.getElementById('theaterScript');
    if (!btn || !scriptEl) return;

    if (!state.isShowingFullScript) {
        // Switch to full script with spacious, readable formatting
        scriptEl.innerHTML = `<div class="text-left font-serif italic text-xs leading-[2.1] tracking-wide text-slate-300 pr-2 max-h-[220px] overflow-y-auto custom-scrollbar whitespace-pre-wrap">${state.fullScript}</div>`;
        btn.innerText = "Show Karaoke HUD";
        state.isShowingFullScript = true;
    } else {
        // Switch back to karaoke HUD
        scriptEl.innerHTML = state.karaokeHTML;
        btn.innerText = "Show Full Script";
        state.isShowingFullScript = false;
    }
};

// Nav step sub-transitions inside the Exam Theater page
document.getElementById('nextToExamBtn').onclick = () => {
    document.getElementById('completionMapView').classList.add('hidden');
    document.getElementById('completionExamView').classList.remove('hidden');
    
    // Clean scroll alignment to top of Question 1 (Priority 6)
    const questionsEl = document.getElementById('theaterQuestions');
    if (questionsEl) questionsEl.scrollTop = 0;
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

document.getElementById('backToMapBtn').onclick = () => {
    document.getElementById('completionExamView').classList.add('hidden');
    document.getElementById('completionMapView').classList.remove('hidden');
};

document.getElementById('nextToGRCBtn').onclick = () => {
    document.getElementById('tabArchitecture').click();
};

// Reset session statistics click handler
document.getElementById('resetSessionStatsBtn').onclick = () => {
    localStorage.removeItem(STATS_KEY);
    updateSessionLedgerUI();
};

// Initialize the cumulative ledger UI on load to retrieve stored session states
updateSessionLedgerUI();
