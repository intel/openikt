<template>
  <h1 class="page-title">OpenIKT</h1>
</template>

<script>
export default {
  name: 'PageTitle',
  mounted() {
    const titleEl = document.querySelector('.page-title')
    titleEl.innerHTML = titleEl.textContent.replace(/\S/g, '<span>$&</span>')

    let delay = 0
    const spansEl = document.querySelectorAll('span')
    spansEl.forEach((itemEl, index) => {
      delay += 0.1
      if (index === 4) {
        delay += 0.3
      }
      itemEl.style.setProperty('--delay', `${delay}s`)
    })

    titleEl.addEventListener('animationend', function (e) {
      if (e.target === document.querySelector('h1 span:last-child')) {
        this.classList.add('ended')
      }
    })
  }
}
</script>

<style lang="scss" scoped>
.page-title {
  position: relative;
  font-size: 36px;
  font-family: monospace;
  padding: 0;

  &::after {
    content: '';
    position: absolute;
    width: 10px;
    height: 36px;
    top: 0;
    right: -10px;
    background-color: #000;
  }

  &.ended::after {
    animation: cursor 1s steps(2, jump-none) infinite;
  }

  ::v-deep span {
    --delay: 999s;
    display: inline-block;
    width: 0ch;
    overflow: hidden;
    animation: text-in 0.1s ease-in-out forwards;
    animation-delay: var(--delay);
  }
}

@keyframes cursor {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes text-in {
  from {
    width: 0ch;
  }

  to {
    width: 1ch;
  }
}
</style>
