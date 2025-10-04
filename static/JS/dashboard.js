// ====== Modern dropdown for STATUS in .lt-pill ======
(function () {
  const ENHANCED_FLAG = 'data-enhanced';

  function enhancePill(pill) {
    if (!pill || pill.getAttribute(ENHANCED_FLAG) === '1') return;
    const native = pill.querySelector('select.lt-select');
    if (!native) return;

    pill.setAttribute(ENHANCED_FLAG, '1');
    pill.classList.add('lt-dd'); // wrapper stanu

    // widoczna etykieta
    const toggle = document.createElement('span');
    toggle.className = 'lt-dd-toggle';
    toggle.tabIndex = 0;

    const caret = pill.querySelector('.lt-caret') || pill.appendChild(document.createElement('span'));
    caret.classList.add('lt-caret');

    pill.insertBefore(toggle, caret);

    // menu
    const menu = document.createElement('div');
    menu.className = 'lt-dd-menu';
    pill.appendChild(menu);

    const buildItems = () => {
      menu.innerHTML = '';
      [...native.options].forEach(opt => {
        const item = document.createElement('div');
        item.className = 'lt-dd-item';
        item.setAttribute('role', 'option');
        item.dataset.value = opt.value;

        const badge = document.createElement('span');
        badge.className = `lt-dd-badge badge-${opt.value}`;
        badge.textContent = opt.value;

        const label = document.createElement('span');
        label.textContent = opt.textContent;

        item.appendChild(badge);
        item.appendChild(label);
        if (opt.selected) item.setAttribute('aria-selected', 'true');
        item.addEventListener('click', () => selectValue(opt.value));
        menu.appendChild(item);
      });
    };

    const paintChip = () => {
      pill.classList.remove('status-PL', 'status-PA', 'status-LO');
      if (native.value) pill.classList.add('status-' + native.value);
    };

    const refreshLabel = () => {
      toggle.textContent = native.options[native.selectedIndex]?.text || native.value || '—';
    };

    const markSelected = () => {
      menu.querySelectorAll('.lt-dd-item').forEach(el => {
        el.toggleAttribute('aria-selected', el.dataset.value === native.value);
      });
    };

    const open  = () => pill.classList.add('open');
    const close = () => pill.classList.remove('open');
    const toggleOpen = () => (pill.classList.contains('open') ? close() : open());

    const selectValue = (val) => {
      if (native.value !== val) {
        native.value = val;
        native.dispatchEvent(new Event('change', { bubbles: true }));
      }
      close(); markSelected(); refreshLabel(); paintChip();
    };

    // interakcje
    pill.addEventListener('click', (e) => {
      if (e.target.closest('.lt-dd-menu')) return;
      toggleOpen();
    });

    toggle.addEventListener('keydown', (e) => {
      const items = [...menu.querySelectorAll('.lt-dd-item')];
      const cur = items.findIndex(i => i.dataset.value === native.value);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (!pill.classList.contains('open')) { open(); return; }
        const next = items[Math.min(cur + 1, items.length - 1)];
        if (next) selectValue(next.dataset.value);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (!pill.classList.contains('open')) { open(); return; }
        const prev = items[Math.max(cur - 1, 0)];
        if (prev) selectValue(prev.dataset.value);
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault(); toggleOpen();
      } else if (e.key === 'Escape') {
        close();
      }
    });

    // klik poza – zamknij
    document.addEventListener('click', (e) => {
      if (!pill.contains(e.target)) close();
    });

    native.addEventListener('change', () => { markSelected(); refreshLabel(); paintChip(); });

    // init
    buildItems(); refreshLabel(); paintChip(); markSelected();
  }

  function enhanceAll() {
    document.querySelectorAll('.lt-pill').forEach(enhancePill);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', enhanceAll, { once: true });
  } else {
    enhanceAll();
  }
  window.addEventListener('load', enhanceAll, { once: true });

  const mo = new MutationObserver((muts) => {
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (!(n instanceof Element)) continue;
        if (n.matches?.('.lt-pill')) enhancePill(n);
        n.querySelectorAll?.('.lt-pill').forEach(enhancePill);
      }
    }
  });
  mo.observe(document.documentElement, { childList: true, subtree: true });

  window.LT_enhanceStatusPills = enhanceAll;
})();


// ===== AUTOSAVE dla wierszy (EDIT i CREATE) =====
//
// – działa dla inputów: planned, done, lo_code, picker
// – odnajduje formularz przez `HTMLInputElement.form` (czyli zadziała dla row-… i create-…)
// – debouncing 500 ms per–formularz

document.addEventListener('DOMContentLoaded', () => {
  const NAME_SELECTOR = 'input[name="planned"], input[name="done"], input[name="lo_code"], input[name="picker"]';
  const inputs = document.querySelectorAll('.lt-table tbody ' + NAME_SELECTOR);

  // osobny timer dla każdego formularza
  const timers = new WeakMap();

  function submitDebounced(form) {
    if (!form) return;
    const prev = timers.get(form);
    if (prev) clearTimeout(prev);
    const t = setTimeout(() => {
      try {
        // dodaj delikatny stan „zapisywanie"
        form.classList.add('is-saving');
        
        // AJAX POST zamiast form.requestSubmit() - bez przeładowania strony
        const formData = new FormData(form);
        const loadId = form.action.split('/').pop();
        
        fetch(form.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(response => {
          if (response.ok) {
            // Pokaż wizualną informację o zapisaniu
            const input = form.querySelector('input:focus');
            if (input) {
              input.style.backgroundColor = '#d4edda';
              setTimeout(() => {
                input.style.backgroundColor = '';
              }, 1000);
            }
          } else {
            console.error('Błąd zapisu:', response.statusText);
          }
        })
        .catch(error => {
          console.error('Błąd sieci:', error);
        })
        .finally(() => {
          setTimeout(() => form.classList.remove('is-saving'), 1000);
        });
        
      } catch (error) {
        console.error('Błąd:', error);
        form.classList.remove('is-saving');
      }
    }, 1000); // Zwiększony timeout na 1 sekundę
    timers.set(form, t);
  }

  inputs.forEach(inp => {
    // Najpewniej: input.form zwraca powiązany <form> (także gdy form jest poza wierszem)
    const getForm = () => inp.form
      || inp.closest('tr')?.querySelector('form')      // awaryjnie
      || inp.closest('form');                           // ostatnia deska

    const handler = () => submitDebounced(getForm());
    inp.addEventListener('input', handler);
    inp.addEventListener('change', handler);
  });

  // ====== Obsługa zmiany statusu - pokaż/ukryj przycisk WYCZYŚĆ ======
  const statusSelects = document.querySelectorAll('select[name="status"]:not([disabled])');
  statusSelects.forEach(select => {
    select.addEventListener('change', function() {
      const laneCard = this.closest('.lt-lane');
      const timeSlot = laneCard.dataset.time;
      const lane = laneCard.dataset.lane;
      const clearButtonField = document.getElementById(`clear-btn-${timeSlot}-${lane}`);
      
      if (this.value === 'LO') {
        // Pokaż przycisk WYCZYŚĆ natychmiastowo
        if (clearButtonField) {
          clearButtonField.style.display = 'block';
        }
      } else {
        // Ukryj przycisk WYCZYŚĆ natychmiastowo
        if (clearButtonField) {
          clearButtonField.style.display = 'none';
        }
      }
    });
  });
});

// ====== Funkcja czyszczenia danych w kolumnie ======
function clearLaneData(timeSlot, lane) {
  if (!confirm(`Czy na pewno chcesz wyczyścić wszystkie dane w kolumnie ${lane} dla czasu ${timeSlot}?`)) {
    return;
  }

  // Utwórz formularz do wysłania POST request
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/loads/clear_lane';
  
  // Dodaj ukryte pola
  const timeInput = document.createElement('input');
  timeInput.type = 'hidden';
  timeInput.name = 'time_slot';
  timeInput.value = timeSlot;
  form.appendChild(timeInput);
  
  const laneInput = document.createElement('input');
  laneInput.type = 'hidden';
  laneInput.name = 'lane';
  laneInput.value = lane;
  form.appendChild(laneInput);
  
  // Dodaj formularz do body i wyślij
  document.body.appendChild(form);
  form.submit();
}

// ====== Kolorowanie wierszy dla Picking Active ======
function updateRowColors() {
  console.log('updateRowColors called');
  
  // Znajdź wszystkie karty (lane)
  const laneCards = document.querySelectorAll('.lt-lane');
  console.log('Found lane cards:', laneCards.length);
  
  // Najpierw usuń wszystkie klasy kolorowania
  laneCards.forEach(card => {
    const rows = card.querySelectorAll('tbody tr');
    rows.forEach(row => {
      row.classList.remove('picking-active-row', 'conflict-row', 'completed-row');
    });
  });
  
  // Znajdź karty z statusem Picking Active
  const pickingActiveCards = Array.from(laneCards).filter(card => {
    const statusSelect = card.querySelector('select[name="status"]');
    let status = 'PL';
    
    if (statusSelect) {
      // Sprawdź czy select jest disabled
      if (statusSelect.disabled) {
        // Dla disabled selectów, sprawdź selected option
        const selectedOption = statusSelect.querySelector('option[selected]');
        status = selectedOption ? selectedOption.value : 'PL';
      } else {
        // Dla aktywnych selectów, użyj value
        status = statusSelect.value;
      }
    }
    
    console.log('Checking card status:', status, 'Element:', card);
    return status === 'PA';
  });
  
  // Znajdź karty z statusem Planned
  const plannedCards = Array.from(laneCards).filter(card => {
    const statusSelect = card.querySelector('select[name="status"]');
    let status = 'PL';
    
    if (statusSelect) {
      // Sprawdź czy select jest disabled
      if (statusSelect.disabled) {
        // Dla disabled selectów, sprawdź selected option
        const selectedOption = statusSelect.querySelector('option[selected]');
        status = selectedOption ? selectedOption.value : 'PL';
      } else {
        // Dla aktywnych selectów, użyj value
        status = statusSelect.value;
      }
    }
    
    console.log('Checking card status:', status, 'Element:', card);
    return status === 'PL';
  });
  
  console.log('Picking Active cards:', pickingActiveCards.length);
  console.log('Planned cards:', plannedCards.length);
  
       // Sprawdź konflikty między kartami
       if (pickingActiveCards.length > 0 && plannedCards.length > 0) {
         checkForConflicts(pickingActiveCards, plannedCards);
       }
       
       // Sprawdź zaawansowane konflikty (3 karty)
       if (pickingActiveCards.length > 0 && plannedCards.length > 1) {
         checkAdvancedConflicts(pickingActiveCards, plannedCards);
       }
  
  // Kolorowanie wierszy dla Picking Active
  laneCards.forEach(card => {
    const statusSelect = card.querySelector('select[name="status"]');
    const status = statusSelect ? statusSelect.value : 'PL';
    
    const rows = card.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
      const plannedInput = row.querySelector('input[name="planned"]');
      const doneInput = row.querySelector('input[name="done"]');
      const plannedValue = plannedInput ? parseInt(plannedInput.value) || 0 : 0;
      const doneValue = doneInput ? parseInt(doneInput.value) || 0 : 0;
      const hasPlannedValue = plannedValue > 0;
      
      if (status === 'PA' && hasPlannedValue) {
        // Sprawdź czy wiersz jest zakończony (planned = done)
        if (plannedValue > 0 && doneValue > 0 && plannedValue === doneValue) {
          row.classList.add('completed-row');
          console.log(`Row completed: Planned=${plannedValue}, Done=${doneValue}`);
        } else {
          row.classList.add('picking-active-row');
        }
      }
    });
  });
}

// ====== Sprawdzanie konfliktów między kartami ======
function checkForConflicts(pickingActiveCards, plannedCards) {
  console.log('Checking for conflicts...');
  console.log('PA Cards found:', pickingActiveCards.length);
  console.log('Planned Cards found:', plannedCards.length);
  
  pickingActiveCards.forEach((paCard, paIndex) => {
    console.log(`Processing PA Card ${paIndex + 1}`, paCard);
    const paRows = paCard.querySelectorAll('tbody tr');
    console.log(`PA Card has ${paRows.length} rows`);
    
    paRows.forEach((paRow, paRowIndex) => {
      console.log(`Processing PA Row ${paRowIndex + 1}`);
      
      // Sprawdź wszystkie komórki w wierszu
      const cells = paRow.querySelectorAll('td');
      console.log(`PA Row has ${cells.length} cells`);
      cells.forEach((cell, cellIndex) => {
        console.log(`PA Cell ${cellIndex + 1}: "${cell.textContent?.trim()}"`);
      });
      
             const paSeq = paRow.querySelector('td:nth-child(3)')?.textContent?.trim(); // SEQ kolumna
      const paPlannedInput = paRow.querySelector('input[name="planned"]');
      const paPlannedValue = paPlannedInput ? parseInt(paPlannedInput.value) || 0 : 0;
      const paDoneInput = paRow.querySelector('input[name="done"]');
      const paDoneValue = paDoneInput ? parseInt(paDoneInput.value) || 0 : 0;
      
      console.log(`PA Row ${paRowIndex + 1} - DEBUG:`, {
        rowElement: paRow,
        seq: paSeq,
        plannedInput: paPlannedInput,
        plannedInputValue: paPlannedInput ? paPlannedInput.value : 'null',
        plannedValue: paPlannedValue
      });
      
      console.log(`PA Row ${paRowIndex + 1} - Input elements:`, {
        plannedInput: paPlannedInput,
        plannedValue: paPlannedValue,
        plannedInputValue: paPlannedInput ? paPlannedInput.value : 'null',
        doneInput: paDoneInput,
        doneValue: paDoneValue,
        doneInputValue: paDoneInput ? paDoneInput.value : 'null'
      });
      
      console.log(`PA Row ${paRowIndex + 1} - SEQ: "${paSeq}", Planned: ${paPlannedValue}, Done: ${paDoneValue}`);
      
      if (!paSeq || paPlannedValue <= 0) {
        console.log(`PA Row ${paRowIndex + 1} - Skipping (no SEQ or planned value)`);
        return;
      }
      
      // Sprawdź czy done >= planned (nie koloruj jeśli tak)
      if (paDoneValue >= paPlannedValue) {
        console.log(`PA Row ${paRowIndex + 1} - Done (${paDoneValue}) >= Planned (${paPlannedValue}), skipping conflict check`);
        return;
      }
      
      console.log(`PA Row ${paRowIndex + 1} - Will check for conflicts with planned cards`);
      
      // Sprawdź konflikty z kartami Planned
      plannedCards.forEach((plannedCard, plannedIndex) => {
        console.log(`Checking against Planned Card ${plannedIndex + 1}`, plannedCard);
        const plannedRows = plannedCard.querySelectorAll('tbody tr');
        console.log(`Planned Card has ${plannedRows.length} rows`);
        
        plannedRows.forEach((plannedRow, plannedRowIndex) => {
          console.log(`Processing Planned Row ${plannedRowIndex + 1}`);
          
          // Sprawdź wszystkie komórki w wierszu
          const plannedCells = plannedRow.querySelectorAll('td');
          console.log(`Planned Row has ${plannedCells.length} cells`);
          plannedCells.forEach((cell, cellIndex) => {
            console.log(`Planned Cell ${cellIndex + 1}: "${cell.textContent?.trim()}"`);
          });
          
                 const plannedSeq = plannedRow.querySelector('td:nth-child(3)')?.textContent?.trim();
          const plannedPlannedInput = plannedRow.querySelector('input[name="planned"]');
          const plannedPlannedValue = plannedPlannedInput ? parseInt(plannedPlannedInput.value) || 0 : 0;
          
          console.log(`Planned Row ${plannedRowIndex + 1} - DEBUG:`, {
            rowElement: plannedRow,
            seq: plannedSeq,
            plannedInput: plannedPlannedInput,
            plannedInputValue: plannedPlannedInput ? plannedPlannedInput.value : 'null',
            plannedValue: plannedPlannedValue
          });
          
          console.log(`Planned Row ${plannedRowIndex + 1} - Input elements:`, {
            plannedInput: plannedPlannedInput,
            plannedValue: plannedPlannedValue,
            plannedInputValue: plannedPlannedInput ? plannedPlannedInput.value : 'null'
          });
          
          console.log(`Planned Row ${plannedRowIndex + 1} - SEQ: "${plannedSeq}", Planned: ${plannedPlannedValue}`);
          
          if (!plannedSeq || plannedPlannedValue <= 0) {
            console.log(`Planned Row ${plannedRowIndex + 1} - Skipping (no SEQ or planned value)`);
            return;
          }
          
          console.log(`Comparing: PA SEQ "${paSeq}" vs Planned SEQ "${plannedSeq}"`);
          console.log(`Comparing: PA Planned ${paPlannedValue} vs Planned Planned ${plannedPlannedValue}`);
          
          // Sprawdź czy SEQ się pokrywa i czy oba wiersze mają wartości w DO ZROBIENIA
          if (paSeq === plannedSeq && paPlannedValue > 0 && plannedPlannedValue > 0) {
            console.log(`🎯 CONFLICT FOUND! PA Row ${paRowIndex + 1} vs Planned Row ${plannedRowIndex + 1}`);
            console.log(`SEQ: "${paSeq}", PA Planned: ${paPlannedValue}, Planned Planned: ${plannedPlannedValue}`);
            plannedRow.classList.add('conflict-row');
            console.log(`Added conflict-row class to planned row`);
          } else {
            console.log(`No conflict between PA Row ${paRowIndex + 1} and Planned Row ${plannedRowIndex + 1}`);
          }
        });
      });
    });
  });
}

// ====== Zaawansowane sprawdzanie konfliktów (3 karty) ======
function checkAdvancedConflicts(pickingActiveCards, plannedCards) {
  console.log('Checking advanced conflicts...');
  console.log('PA Cards:', pickingActiveCards.length);
  console.log('Planned Cards:', plannedCards.length);
  
  // Sprawdź każdą kartę PA
  pickingActiveCards.forEach((paCard, paIndex) => {
    console.log(`Processing PA Card ${paIndex + 1} for advanced conflicts`);
    const paRows = paCard.querySelectorAll('tbody tr');
    
    paRows.forEach((paRow, paRowIndex) => {
      const paSeq = paRow.querySelector('td:nth-child(3)')?.textContent?.trim();
      const paPlannedInput = paRow.querySelector('input[name="planned"]');
      const paPlannedValue = paPlannedInput ? parseInt(paPlannedInput.value) || 0 : 0;
      const paDoneInput = paRow.querySelector('input[name="done"]');
      const paDoneValue = paDoneInput ? parseInt(paDoneInput.value) || 0 : 0;
      
      console.log(`PA Row ${paRowIndex + 1} - SEQ: "${paSeq}", Planned: ${paPlannedValue}, Done: ${paDoneValue}`);
      
      // Sprawdź czy PA ma planned = done (zakończone)
      if (paSeq && paPlannedValue > 0 && paDoneValue > 0 && paPlannedValue === paDoneValue) {
        console.log(`PA Row ${paRowIndex + 1} - COMPLETED (Planned = Done), checking if should remove conflicts`);
        
        // Sprawdź czy są inne karty Planned z tym samym SEQ
        let hasOtherPlannedWithSameSeq = false;
        plannedCards.forEach((plannedCard, plannedIndex) => {
          const plannedRows = plannedCard.querySelectorAll('tbody tr');
          plannedRows.forEach((plannedRow, plannedRowIndex) => {
            const plannedSeq = plannedRow.querySelector('td:nth-child(3)')?.textContent?.trim();
            const plannedPlannedInput = plannedRow.querySelector('input[name="planned"]');
            const plannedPlannedValue = plannedPlannedInput ? parseInt(plannedPlannedInput.value) || 0 : 0;
            
            if (plannedSeq === paSeq && plannedPlannedValue > 0) {
              console.log(`Found other Planned card with same SEQ "${plannedSeq}" and value ${plannedPlannedValue}`);
              hasOtherPlannedWithSameSeq = true;
            }
          });
        });
        
        // Jeśli nie ma innych Planned z tym samym SEQ, usuń konflikt
        if (!hasOtherPlannedWithSameSeq) {
          console.log(`Removing conflict for PA Row ${paRowIndex + 1} - no other Planned cards with same SEQ`);
          
          // Usuń czerwone kolorowanie ze wszystkich Planned kart dla tego SEQ
          plannedCards.forEach(plannedCard => {
            const plannedRows = plannedCard.querySelectorAll('tbody tr');
            plannedRows.forEach(plannedRow => {
              const plannedSeq = plannedRow.querySelector('td:nth-child(3)')?.textContent?.trim();
              if (plannedSeq === paSeq) {
                plannedRow.classList.remove('conflict-row');
                console.log(`Removed conflict-row class from Planned row with SEQ "${plannedSeq}"`);
              }
            });
          });
        } else {
          console.log(`Keeping conflict for PA Row ${paRowIndex + 1} - other Planned cards exist with same SEQ`);
        }
      }
    });
  });
}

// Uruchom kolorowanie przy załadowaniu strony
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOMContentLoaded - starting updateRowColors');
  updateRowColors();
});

// Uruchom kolorowanie po zmianie statusu
document.addEventListener('change', function(e) {
  console.log('Change event detected:', e.target.name, e.target.value);
  if (e.target.name === 'status') {
    console.log('Status changed, updating row colors');
    updateRowColors();
  }
});

// Debouncing dla kolorowania
let colorUpdateTimeout;
function debouncedUpdateRowColors() {
  clearTimeout(colorUpdateTimeout);
  colorUpdateTimeout = setTimeout(() => {
    console.log('Debounced updateRowColors called');
    updateRowColors();
  }, 500); // 500ms opóźnienie
}

// Uruchom kolorowanie po zmianie wartości w polach
document.addEventListener('input', function(e) {
  console.log('Input event detected:', e.target.name, e.target.value);
  if (e.target.name === 'planned' || e.target.name === 'done') {
    console.log('Planned or Done input changed, debounced updating row colors');
    debouncedUpdateRowColors();
  }
});

// Dodatkowe debugowanie - sprawdź czy funkcja jest dostępna globalnie
window.updateRowColors = updateRowColors;
window.testConflictDetection = function() {
  console.log('=== TESTING CONFLICT DETECTION ===');
  
  // Sprawdź czy są karty
  const laneCards = document.querySelectorAll('.lt-lane');
  console.log('Total lane cards found:', laneCards.length);
  
  // Sprawdź statusy
  laneCards.forEach((card, index) => {
    const statusSelect = card.querySelector('select[name="status"]');
    const status = statusSelect ? statusSelect.value : 'PL';
    console.log(`Card ${index + 1} status:`, status);
  });
  
  // Sprawdź wiersze
  laneCards.forEach((card, index) => {
    const rows = card.querySelectorAll('tbody tr');
    console.log(`Card ${index + 1} has ${rows.length} rows`);
    
    rows.forEach((row, rowIndex) => {
      const seq = row.querySelector('td:nth-child(3)')?.textContent?.trim();
      const plannedInput = row.querySelector('input[name="planned"]');
      const plannedValue = plannedInput ? parseInt(plannedInput.value) || 0 : 0;
      const doneInput = row.querySelector('input[name="done"]');
      const doneValue = doneInput ? parseInt(doneInput.value) || 0 : 0;
      
      console.log(`Card ${index + 1}, Row ${rowIndex + 1}: SEQ="${seq}", Planned=${plannedValue}, Done=${doneValue}`);
    });
  });
  
  // Uruchom funkcję
  updateRowColors();
};

// Dodatkowa funkcja do testowania wartości w inputach
window.testInputValues = function() {
  console.log('=== TESTING INPUT VALUES ===');
  
  const laneCards = document.querySelectorAll('.lt-lane');
  
  laneCards.forEach((card, cardIndex) => {
    const statusSelect = card.querySelector('select[name="status"]');
    const status = statusSelect ? statusSelect.value : 'PL';
    console.log(`\n--- Card ${cardIndex + 1} (${status}) ---`);
    
    const rows = card.querySelectorAll('tbody tr');
    
    rows.forEach((row, rowIndex) => {
      const seq = row.querySelector('td:nth-child(3)')?.textContent?.trim();
      const plannedInput = row.querySelector('input[name="planned"]');
      const doneInput = row.querySelector('input[name="done"]');
      
      console.log(`Row ${rowIndex + 1} (SEQ: ${seq}):`);
      console.log(`  Planned input:`, plannedInput);
      console.log(`  Planned value:`, plannedInput ? plannedInput.value : 'null');
      console.log(`  Planned parsed:`, plannedInput ? parseInt(plannedInput.value) || 0 : 0);
      console.log(`  Done input:`, doneInput);
      console.log(`  Done value:`, doneInput ? doneInput.value : 'null');
      console.log(`  Done parsed:`, doneInput ? parseInt(doneInput.value) || 0 : 0);
    });
  });
};

console.log('updateRowColors function is now available globally');
console.log('testConflictDetection function is now available globally');
console.log('testInputValues function is now available globally');