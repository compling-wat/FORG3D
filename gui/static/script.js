// Object Selector Functionality
let objectsData = {}
let selectedObjects = {
    single: [],
    multiple: []
}

// Initialize object selectors when the page loads
async function initObjectSelectors() {
    try {
        const response = await fetch('/api/objects')
        const data = await response.json()
        
        if (data.success) {
            objectsData = data.objects
            populateObjectDropdowns()
            initDropdownEventListeners()
        } else {
            console.error('Failed to load objects:', data.error)
            showObjectLoadError()
        }
    } catch (error) {
        console.error('Error fetching objects:', error)
        showObjectLoadError()
    }
}

function showObjectLoadError() {
    const singleToggle = document.getElementById('objects-single-toggle')
    const multipleToggle = document.getElementById('objects-multiple-toggle')
    
    if (singleToggle) {
        singleToggle.querySelector('.dropdown-text').textContent = 'Failed to load objects'
        singleToggle.disabled = true
    }
    if (multipleToggle) {
        multipleToggle.querySelector('.dropdown-text').textContent = 'Failed to load objects'
        multipleToggle.disabled = true
    }
}

function populateObjectDropdowns() {
    populateObjectDropdown('single')
    populateObjectDropdown('multiple')
    updateDropdownTexts()
}

function populateObjectDropdown(type) {
    const menu = document.getElementById(`objects-${type}-menu`)
    if (!menu) return
    
    menu.innerHTML = ''
    
    Object.entries(objectsData).forEach(([key, obj]) => {
        const option = document.createElement('div')
        option.className = 'object-option'
        option.innerHTML = `
            <input type="checkbox" id="${type}-${key}" data-object="${key}" data-type="${type}">
            <div class="object-info" style="font-size: 0.875rem">
                <div class="object-name">${obj.name}</div>
                <div class="object-details" style="font-size: 0.75rem">
                    <span class="object-group">${obj.group}</span>
                    ${obj.default_orientation ? `Default: ${obj.default_orientation}` : 'No default orientation'}
                </div>
            </div>
        `
        
        const checkbox = option.querySelector('input[type="checkbox"]')
        checkbox.addEventListener('change', (e) => handleObjectSelection(e, type, key))
        
        menu.appendChild(option)
    })
}

function initDropdownEventListeners() {
    // Single render dropdown
    const singleToggle = document.getElementById('objects-single-toggle')
    const singleMenu = document.getElementById('objects-single-menu')
    
    if (singleToggle && singleMenu) {
        singleToggle.addEventListener('click', (e) => {
            e.stopPropagation()
            toggleDropdown('single')
        })
    }
    
    // Multiple render dropdown
    const multipleToggle = document.getElementById('objects-multiple-toggle')
    const multipleMenu = document.getElementById('objects-multiple-menu')
    
    if (multipleToggle && multipleMenu) {
        multipleToggle.addEventListener('click', (e) => {
            e.stopPropagation()
            toggleDropdown('multiple')
        })
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        closeAllDropdowns()
    })
    
    // Prevent dropdown from closing when clicking inside
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', (e) => {
            e.stopPropagation()
        })
    })
}

function toggleDropdown(type) {
    const toggle = document.getElementById(`objects-${type}-toggle`)
    const menu = document.getElementById(`objects-${type}-menu`)
    
    if (!toggle || !menu) return
    
    const isOpen = menu.classList.contains('open')
    
    // Close all dropdowns first
    closeAllDropdowns()
    
    // Toggle this dropdown
    if (!isOpen) {
        toggle.classList.add('active')
        menu.classList.add('open')
    }
}

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.classList.remove('active')
    })
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('open')
    })
}

function handleObjectSelection(event, type, objectKey) {
    const isChecked = event.target.checked
    
    if (isChecked) {
        // Check selection limits
        if (type === 'single' && selectedObjects.single.length >= 2) {
            event.preventDefault()
            event.target.checked = false
            alert('You can only select 2 objects for single render')
            return
        }
        
        selectedObjects[type].push(objectKey)
    } else {
        selectedObjects[type] = selectedObjects[type].filter(key => key !== objectKey)
    }
    
    updateSelectedObjectsDisplay(type)
    updateDropdownTexts()
}

function removeSelectedObject(type, objectKey) {
    selectedObjects[type] = selectedObjects[type].filter(key => key !== objectKey)
    
    // Uncheck the checkbox
    const checkbox = document.getElementById(`${type}-${objectKey}`)
    if (checkbox) {
        checkbox.checked = false
    }
    
    updateSelectedObjectsDisplay(type)
    updateDropdownTexts()
}

function updateSelectedObjectsDisplay(type) {
    const container = document.getElementById(`objects-${type}-selected`)
    if (!container) return
    
    if (selectedObjects[type].length === 0) {
        container.innerHTML = ''
        return
    }
    
    container.innerHTML = selectedObjects[type].map(objectKey => {
        const obj = objectsData[objectKey]
        return `
            <div class="selected-object-tag">
                <span>${obj.name}</span>
                <button type="button" class="remove-object" onclick="removeSelectedObject('${type}', '${objectKey}')">×</button>
            </div>
        `
    }).join('')
}

function updateDropdownTexts() {
    // Update single render dropdown text
    const singleToggle = document.getElementById('objects-single-toggle')
    if (singleToggle) {
        const count = selectedObjects.single.length
        const text = count === 0 
            ? 'Select objects...' 
            : `${count}/2 objects selected`
        singleToggle.querySelector('.dropdown-text').textContent = text
    }
    
    // Update multiple render dropdown text
    const multipleToggle = document.getElementById('objects-multiple-toggle')
    if (multipleToggle) {
        const count = selectedObjects.multiple.length
        const text = count === 0 
            ? 'Select objects...' 
            : `${count} objects selected`
        multipleToggle.querySelector('.dropdown-text').textContent = text
    }
}



// Get selected objects for form submission
function getSelectedObjectsString(type) {
    return selectedObjects[type].join(' ')
}

// DOM elements
const renderTabs = document.querySelectorAll(".render-tab")
const renderForms = document.querySelectorAll(".render-form")
const singleForm = document.getElementById("single-render-form")
const multipleForm = document.getElementById("multiple-render-form")
const backgroundForm = document.getElementById("background-generation-form")
const outputDiv = document.getElementById("output")
const outputStatus = document.getElementById("output-status")
const singleSubmitBtn = document.getElementById("single-submit-btn")
const multipleSubmitBtn = document.getElementById("multiple-submit-btn")
const backgroundSubmitBtn = document.getElementById("background-submit-btn")
const stopBtn = document.getElementById("stop-btn")

// WebSocket connection
let socket = null
let isConnected = false
let isProcessRunning = false

// Initialize WebSocket connection
function initWebSocket() {
  // Connect to WebSocket server
  socket = io()
  
  socket.on('connect', () => {
    console.log('WebSocket connected')
    isConnected = true
  })
  
  socket.on('disconnect', () => {
    console.log('WebSocket disconnected')
    isConnected = false
  })
  
  socket.on('script_started', (data) => {
    console.log('Script started:', data.message)
    appendOutput(`🚀 ${data.message}\n`)
    isProcessRunning = true
    stopBtn.classList.remove('hidden')
  })
  
  socket.on('script_output', (data) => {
    const prefix = data.type === 'stderr' ? '' : '📝 '
    appendOutput(`${prefix}${data.data}\n`)
  })
  
  socket.on('script_completed', (data) => {
    isProcessRunning = false
    stopBtn.classList.add('hidden')
    
    if (data.success) {
      outputStatus.textContent = "Completed"
      outputStatus.style.background = "var(--bg-success)"
      outputStatus.style.color = "white"
      appendOutput(`✅ ${data.message}\n`)
    } else {
      outputStatus.textContent = "Failed"
      outputStatus.style.background = "var(--bg-error)"
      outputStatus.style.color = "white"
      appendOutput(`${data.message}\n`)
    }
    
    // Re-enable submit buttons
    singleSubmitBtn.disabled = false
    multipleSubmitBtn.disabled = false
    backgroundSubmitBtn.disabled = false
    singleSubmitBtn.innerHTML = `<span class="btn-icon">▶</span>Run Single Render`
    multipleSubmitBtn.innerHTML = `<span class="btn-icon">▶</span>Run Multiple Renders`
    backgroundSubmitBtn.innerHTML = `<span class="btn-icon">🎨</span>Generate Backgrounds`
  })
  
  socket.on('script_error', (data) => {
    isProcessRunning = false
    stopBtn.classList.add('hidden')
    
    outputStatus.textContent = "Error"
    outputStatus.style.background = "var(--bg-error)"
    outputStatus.style.color = "white"
    appendOutput(`Error: ${data.error}\n`)
    
    // Re-enable submit buttons
    singleSubmitBtn.disabled = false
    multipleSubmitBtn.disabled = false
    backgroundSubmitBtn.disabled = false
    singleSubmitBtn.innerHTML = `<span class="btn-icon">▶</span>Run Single Render`
    multipleSubmitBtn.innerHTML = `<span class="btn-icon">▶</span>Run Multiple Renders`
    backgroundSubmitBtn.innerHTML = `<span class="btn-icon">🎨</span>Generate Backgrounds`
  })

  socket.on('script_stopped', (data) => {
    isProcessRunning = false
    stopBtn.classList.add('hidden')
    stopBtn.disabled = false
    stopBtn.innerHTML = '<span>⏹</span>Stop'
    
    outputStatus.textContent = "Stopped"
    outputStatus.style.background = "var(--bg-warning)"
    outputStatus.style.color = "white"
    appendOutput(`⏹ ${data.message}\n`)
    
    // Re-enable submit buttons
    singleSubmitBtn.disabled = false
    multipleSubmitBtn.disabled = false
    backgroundSubmitBtn.disabled = false
    singleSubmitBtn.innerHTML = `<span class="btn-icon">▶</span>Run Single Render`
    multipleSubmitBtn.innerHTML = `<span class="btn-icon">▶</span>Run Multiple Renders`
    backgroundSubmitBtn.innerHTML = `<span class="btn-icon">🎨</span>Generate Backgrounds`
  })
}

// Function to append output to the output div
function appendOutput(text) {
  outputDiv.textContent += text
  // Auto-scroll to bottom with a small delay to ensure content is rendered
  setTimeout(() => {
    outputDiv.scrollTop = outputDiv.scrollHeight
  }, 10)
}

// Handle tab switching
renderTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const targetForm = tab.getAttribute("data-form")

    // Update active tab
    renderTabs.forEach((t) => t.classList.remove("active"))
    tab.classList.add("active")

    // Show/hide forms with smooth transition
    renderForms.forEach((form) => {
      form.classList.add("hidden")
    })

    setTimeout(() => {
      document.getElementById(targetForm).classList.remove("hidden")
    }, 150)
  })
})

// Enhanced form submission handler with WebSocket
async function handleFormSubmit(event, renderType) {
  event.preventDefault()

  if (!isConnected) {
    appendOutput("WebSocket connection not available. Please refresh the page.\n")
    return
  }

  const submitBtn = event.target.querySelector('button[type="submit"]')
  const originalHTML = submitBtn.innerHTML

  // Show loading state
  submitBtn.disabled = true
  const loadingText = renderType === "background" ? "Generating backgrounds..." : `Processing ${renderType} render...`
  submitBtn.innerHTML = `<span class="loading"></span>${loadingText}`

  // Update status
  outputStatus.textContent = "Processing..."
  outputStatus.style.background = "var(--bg-warning)"
  outputStatus.style.color = "white"

  // Clear previous output and add initial message
  const startText = renderType === "background" ? "Starting background generation..." : `Starting ${renderType} render...`
  outputDiv.textContent = `${startText}\nPlease wait while we process your request...\n\n`

  const formData = new FormData(event.target)
  const data = Object.fromEntries(formData.entries())

  // Handle selected objects from dropdown
  if (renderType === "single" || renderType === "multiple") {
    const selectedObjectsString = getSelectedObjectsString(renderType)
    if (!selectedObjectsString) {
      const minRequired = renderType === "single" ? 2 : 1
      appendOutput(`Error: Please select at least ${minRequired} object${minRequired > 1 ? 's' : ''} for ${renderType} render\n`)
      
      // Re-enable submit button
      submitBtn.disabled = false
      submitBtn.innerHTML = originalHTML
      outputStatus.textContent = "Ready"
      outputStatus.style.background = "var(--bg-secondary)"
      outputStatus.style.color = "var(--text-secondary)"
      return
    }
    data.objects = selectedObjectsString
  }

  // Handle checkbox for multiple renders
  if (renderType === "multiple") {
    data["render-random"] = document.getElementById("render-random").checked
  }

  // Determine script and prepare arguments
  let scriptName = 'render.sh'
  const args = []

  if (renderType === "background") {
    scriptName = 'generate.sh'
    
    args.push('--prompt')
    args.push(data.prompt)
    args.push('--negative_prompt')  
    args.push(data['negative-prompt'])
    args.push('--device')
    args.push(data.device)
  } else {
    // Handle render scripts
    for (const [key, value] of Object.entries(data)) {
      if (value) {
        const argKey = `--${key}`
        
        if (typeof value === "boolean" && value) {
          args.push(argKey)
        } else if (key === "objects") {
          args.push(argKey)
          args.push(...value.split(" "))
        } else if (typeof value !== "boolean") {
          args.push(argKey)
          args.push(String(value))
        }
      }
    }
  }

  // Send script execution request via WebSocket
  socket.emit('start_script', {
    script_name: scriptName,
    args: args
  })
}

// Add form validation
function validateForm(form) {
  const requiredFields = form.querySelectorAll("input[required], select[required]")
  let isValid = true

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      field.style.borderColor = "var(--bg-error)"
      isValid = false
    } else {
      field.style.borderColor = "var(--border-primary)"
    }
  })

  return isValid
}

// Validate object selection
function validateObjectSelection(type) {
  const selected = selectedObjects[type]
  
  if (type === "single") {
    return selected.length === 2
  } else if (type === "multiple") {
    return selected.length > 0
  }
  
  return false
}

// Enhanced form event listeners
singleForm.addEventListener("submit", (e) => {
  if (validateForm(singleForm) && validateObjectSelection("single")) {
    handleFormSubmit(e, "single")
  } else {
    e.preventDefault()
    appendOutput("Please fill in all required fields and select the required objects\n")
  }
})

multipleForm.addEventListener("submit", (e) => {
  if (validateForm(multipleForm) && validateObjectSelection("multiple")) {
    handleFormSubmit(e, "multiple")
  } else {
    e.preventDefault()
    appendOutput("Please fill in all required fields and select the required objects\n")
  }
})

backgroundForm.addEventListener("submit", (e) => {
  if (validateForm(backgroundForm)) {
    handleFormSubmit(e, "background")
  } else {
    e.preventDefault()
    appendOutput("Please fill in all required fields\n")
  }
})

// Add input event listeners for real-time validation feedback
document.querySelectorAll("input, select").forEach((field) => {
  field.addEventListener("input", () => {
    if (field.value.trim()) {
      field.style.borderColor = "var(--border-primary)"
    }
  })

  field.addEventListener("focus", () => {
    field.style.borderColor = "var(--border-accent)"
  })

  field.addEventListener("blur", () => {
    if (!field.value.trim()) {
      field.style.borderColor = "var(--border-primary)"
    }
  })
})


// Initialize tooltips for form hints
document.querySelectorAll(".form-hint").forEach((hint) => {
  hint.addEventListener("mouseenter", (e) => {
    e.target.style.color = "var(--text-secondary)"
  })

  hint.addEventListener("mouseleave", (e) => {
    e.target.style.color = "var(--text-muted)"
  })
})

// Stop button functionality
stopBtn.addEventListener("click", () => {
  if (isProcessRunning && socket && isConnected) {
    socket.emit('stop_script')
    stopBtn.disabled = true
    stopBtn.innerHTML = '<span class="loading"></span>Stopping...'
    appendOutput("🛑 Attempting to stop process...\n")

    setTimeout(() => {
      if (isProcessRunning) {
        stopBtn.disabled = false
        stopBtn.innerHTML = '<span>⏹</span>Stop'
        appendOutput("⚠️ Stop may have failed. Try again if process is still running.\n")
      }
    }, 5000)
  }
})

// Initialize WebSocket connection when page loads
document.addEventListener('DOMContentLoaded', () => {
  initWebSocket()
  initObjectSelectors()
})

console.log("🎬 Blender Render Control initialized successfully!")
