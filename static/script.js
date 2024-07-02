Cookies.set('tz', Intl.DateTimeFormat().resolvedOptions().timeZone)

const grid = $('.grid').masonry({
  itemSelector: '.grid-item',
  columnWidth: '.grid-sizer',
  percentPosition: true,
  gutter: 4
});

grid.imagesLoaded().progress(() => {
  grid.masonry('layout');
});

$(document).on('htmx:afterSettle', (event) => {
  if (event.detail.target.id == 'grid') {
    grid.masonry('reloadItems')
    grid.imagesLoaded().progress(() => {
      grid.masonry('layout');
    });
  }
});

const updateQueryParameter = (key, value) => {
  var url = new URL(window.location.href);
  if (value) {
    url.searchParams.set(key, value);
  } else {
    url.searchParams.delete(key);
  }
  window.location.href = url.toString();
}

$('#timeSelect').on('change', (event) => {
  const time = event.target.value;
  if (time === 'all') {
    updateQueryParameter('today', null);
  } else if (time === 'today') {
    updateQueryParameter('today', 1);
  }
})

$('#groupSelect').on('change', (event) => {
  const groupId = event.target.value;
  if (groupId === '_all') {
    updateQueryParameter('group', null);
  } else {
    updateQueryParameter('group', groupId);
  }
})

$('#sortSelect').on('change', (event) => {
  const sort = event.target.value;
  if (sort === 'desc') {
    updateQueryParameter('sort', null);
  } else if (sort === 'asc') {
    updateQueryParameter('sort', 'asc');
  }
})

const toast = (message) => {
  const toastEl = $('#toast')
  toastEl.addClass('show');
  toastEl.text(message);

  setTimeout(() => {
    toastEl.removeClass('show');
  }, 2500);
}

const addToPocket = async (encoded_url, tag_args) => {
  const response = await fetch(`/actions/pocket?url=${encoded_url}${tag_args}`, {method: 'POST'});
  // addToPocket was not called from htmx
  // hence we need to emulate the behavior of HX-Trigger header so that backend can keep using HX-Trigger
  const hxTrigger = response.headers.get('HX-Trigger');
  if (!hxTrigger) {
    return;
  }
  const parsedHxTrigger = JSON.parse(hxTrigger);
  const toastMessage = parsedHxTrigger.toast;
  if (!toastMessage) {
    return;
  }
  toast(toastMessage);
}

document.body.addEventListener("toast", (event) => {
  toast(event.detail.value);            
})
