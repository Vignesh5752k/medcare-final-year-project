document.addEventListener("DOMContentLoaded", () => {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))
  
    // Animate elements on scroll
    const animateOnScroll = () => {
      const elements = document.querySelectorAll(".feature-card, .product-card, .doctor-card, .testimonial-card")
  
      elements.forEach((element) => {
        const elementPosition = element.getBoundingClientRect().top
        const screenPosition = window.innerHeight / 1.2
  
        if (elementPosition < screenPosition) {
          element.classList.add("fade-in")
        }
      })
    }
  
    // Run on load
    animateOnScroll()
  
    // Run on scroll
    window.addEventListener("scroll", animateOnScroll)
  
    // Quantity increment/decrement
    const quantityInputs = document.querySelectorAll(".quantity-input")
  
    if (quantityInputs) {
      quantityInputs.forEach((input) => {
        const decrementBtn = input.previousElementSibling
        const incrementBtn = input.nextElementSibling
  
        if (decrementBtn && incrementBtn) {
          decrementBtn.addEventListener("click", () => {
            const value = Number.parseInt(input.value)
            if (value > 1) {
              input.value = value - 1
            }
          })
  
          incrementBtn.addEventListener("click", () => {
            const value = Number.parseInt(input.value)
            input.value = value + 1
          })
        }
      })
    }
  
    // Mobile menu toggle
    const navbarToggler = document.querySelector(".navbar-toggler")
    if (navbarToggler) {
      navbarToggler.addEventListener("click", () => {
        document.body.classList.toggle("menu-open")
      })
    }
  
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll(".alert")
    if (flashMessages) {
      flashMessages.forEach((message) => {
        setTimeout(() => {
          const bsAlert = new bootstrap.Alert(message)
          bsAlert.close()
        }, 5000)
      })
    }
  })
  
  