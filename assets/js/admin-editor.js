/* Upgrades the post body textarea to EasyMDE in the Django admin.
   Loaded only by BlogPostAdminForm.Media, never on the public site.

   The editor is attached only while Body Format is Markdown. A legacy HTML post
   gets a plain textarea, because a Markdown toolbar and Markdown live preview
   are both wrong for raw HTML. Switching the dropdown attaches or detaches the
   editor without reloading the page. */
(function () {
  function init() {
    var textarea = document.getElementById('id_body');
    var format = document.getElementById('id_body_format');

    if (!textarea || typeof EasyMDE === 'undefined') {
      return;
    }

    var editor = null;

    function attach() {
      if (editor) {
        return;
      }
      editor = new EasyMDE({
        element: textarea,
        spellChecker: false,
        // Would otherwise pull Font Awesome off a CDN. admin-editor.css gives the
        // toolbar text labels instead.
        autoDownloadFontAwesome: false,
        autosave: { enabled: false },
        indentWithTabs: false,
        tabSize: 2,
        minHeight: '520px',
        // Keeps split view inside the form instead of forcing fullscreen.
        sideBySideFullscreen: false,
        status: ['lines', 'words'],
        toolbar: [
          'bold', 'italic', 'heading', '|',
          'quote', 'unordered-list', 'ordered-list', '|',
          'link', 'image', 'code', 'table', '|',
          'preview', 'side-by-side', 'fullscreen', '|',
          'guide'
        ]
      });
    }

    function detach() {
      if (!editor) {
        return;
      }
      // EasyMDE spells this toTextArea (capital A), inherited from SimpleMDE.
      editor.toTextArea();
      editor = null;
    }

    function sync() {
      if (!format || format.value === 'MD') {
        attach();
      } else {
        detach();
      }
    }

    sync();

    if (format) {
      format.addEventListener('change', sync);
    }
  }

  // Django renders form Media into <head> with no defer attribute, so this file
  // runs before the form fields are parsed. Waiting for the DOM is what makes
  // the lookup above find the textarea instead of null.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
