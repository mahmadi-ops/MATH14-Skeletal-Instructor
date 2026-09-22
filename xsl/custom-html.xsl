<?xml version="1.0" encoding="UTF-8"?>
<!-- Custom HTML conversion:                                                -->
<!--   * render <exercises> divisions (homework) without a number           -->
<!--   * cross-references to figures holding an annotated PreFigure diagram -->
<!--     are plain links, not knowls (see the comment below)                -->
<!--   * every GeoGebra applet, local or by material id, gets a fullscreen -->
<!--     button                                                            -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:pf="https://prefigure.org"
                exclude-result-prefixes="pf"
                version="1.0">
  <xsl:import href="./core/pretext-html.xsl"/>

  <!-- Two extra scripts on every page, both living in assets/ and copied  -->
  <!-- to output as external/.  $html.js.extra only takes ONE file, so the -->
  <!-- core's named template that emits it at the foot of each page is     -->
  <!-- overridden below to emit both:                                      -->
  <!--   * math-input-palette.js - equation-entry palette for the dynamic  -->
  <!--     exercises; targets specific exercises by id and is inert on     -->
  <!--     every other page.                                               -->
  <!--   * custom.js - the floating Socratic AI tutor of the assignment    -->
  <!--     pages; inert on every other page.  It must be a parser-blocking -->
  <!--     script (not deferred) so it can harvest the exercise statements -->
  <!--     while the DOM still holds raw LaTeX, before MathJax typesets.   -->
  <xsl:template name="extra-js-footer">
    <script src="external/math-input-palette.js"></script>
    <script src="external/custom.js"></script>
  </xsl:template>

  <!-- Two extra stylesheets on every page ($html.css.extra is a space-    -->
  <!-- separated list): unnumbered-chapter.css hides the numbers of the    -->
  <!-- "Assignments and Review Problems" chapter, and custom.css styles    -->
  <!-- the AI tutor's floating button and panel.                           -->
  <xsl:param name="html.css.extra" select="'external/unnumbered-chapter.css external/custom.css'"/>

  <xsl:template match="exercises" mode="serial-number"/>
  <xsl:template match="exercises" mode="number"/>

  <!-- In "Assignments and Review Problems" a posted solution is printed     -->
  <!-- straight below its problem instead of being hidden behind a knowl.    -->
  <!-- PreTeXt has a publisher switch for this (knowl/@example-solution),    -->
  <!-- but that is global: it would also unfold the solutions of every       -->
  <!-- worked example in the text.  These templates are the core's own       -->
  <!-- "born visible" branch, restricted to that one chapter.  Which         -->
  <!-- solutions exist at all is decided by <version include="..."/> in      -->
  <!-- publication/publication.ptx.                                          -->
  <xsl:template match="exercise[ancestor::chapter[@xml:id = 'ch-problems']]/solution"
                mode="is-hidden">
    <xsl:text>false</xsl:text>
  </xsl:template>

  <xsl:template match="exercise[ancestor::chapter[@xml:id = 'ch-problems']]/solution"
                mode="heading-birth">
    <xsl:apply-templates select="." mode="heading-non-singleton-number"/>
  </xsl:template>

  <!-- A dynamic <fillin>/<evaluation> exercise swallows its <solution>     -->
  <!-- into the Runestone component data ("solutionHtml"), which the        -->
  <!-- current Runestone runtime never displays: the core's 'fillin' branch -->
  <!-- of exercise-components forwards only the hints to solutions-div.     -->
  <!-- The review problems are dynamic exercises, so their posted solutions -->
  <!-- would be invisible.  This override is the core's branch with the     -->
  <!-- answer and solution forwarded as well, so a posted solution prints   -->
  <!-- beneath its problem exactly as in the fillin-basic assignments.      -->
  <xsl:template match="exercise[@exercise-interactive = 'fillin' and
                                ancestor::chapter[@xml:id = 'ch-problems']]"
                mode="exercise-components">
    <xsl:param name="b-original"/>
    <xsl:param name="block-type"/>
    <xsl:param name="b-has-statement"/>
    <xsl:param name="b-has-hint"/>
    <xsl:param name="b-has-answer"/>
    <xsl:param name="b-has-solution"/>
    <xsl:if test="$b-has-statement">
      <xsl:apply-templates select="." mode="runestone-to-interactive"/>
    </xsl:if>
    <xsl:apply-templates select="." mode="solutions-div">
      <xsl:with-param name="b-original" select="$b-original"/>
      <xsl:with-param name="block-type" select="$block-type"/>
      <xsl:with-param name="b-has-hint" select="$b-has-hint"/>
      <xsl:with-param name="b-has-answer" select="$b-has-answer"/>
      <xsl:with-param name="b-has-solution" select="$b-has-solution"/>
    </xsl:apply-templates>
  </xsl:template>

  <!-- A PreFigure diagram carrying <annotations> is not emitted as an     -->
  <!-- <img>: PreTeXt emits an empty <div class="ChemAccess-element"> that -->
  <!-- the diagcess JS library fills in, and that library only scans the   -->
  <!-- document once, at page load (diagcess.Base.init() in the footer).   -->
  <!-- Knowl content is fetched later, on click, so the container is never -->
  <!-- populated and the reader sees the caption with an empty box where   -->
  <!-- the diagram should be.  Rendering these cross-references as plain   -->
  <!-- links instead sends the reader to the figure itself, in context,    -->
  <!-- where the diagram is present and fully explorable.  Every other     -->
  <!-- cross-reference (equations, examples, unannotated figures, TikZ     -->
  <!-- figures) keeps its knowl.                                           -->
  <!-- The match is on any target containing such a diagram, not just on    -->
  <!-- "figure": an example or task whose solution holds one has the same   -->
  <!-- problem when its own knowl is opened.                                -->
  <xsl:template match="*[.//pf:prefigure/pf:diagram/pf:annotations]"
                mode="xref-as-knowl">
    <xsl:param name="link" select="/.."/>
    <xsl:value-of select="false()"/>
  </xsl:template>

  <!-- Every GeoGebra applet gets GeoGebra's own fullscreen button.        -->
  <!-- The core slate template writes the applet-parameter object inline   -->
  <!-- and offers no hook for extra parameters, so instead of copying the  -->
  <!-- whole template we emit a small shim first and then defer to it via  -->
  <!-- apply-imports.  The shim wraps window.GGBApplet so that any         -->
  <!-- parameter object passing through it picks up                        -->
  <!-- showFullscreenButton: true (unless the author set it).  deployggb   -->
  <!-- loads synchronously in the head, so GGBApplet exists by the time    -->
  <!-- this body script runs; the setter branch covers it loading later.   -->
  <xsl:template match="slate[@surface='geogebra']">
    <script>
<![CDATA[(function () {
  if (window.ggbFullscreenShim) { return; }
  window.ggbFullscreenShim = true;
  var Real = window.GGBApplet || null;
  Object.defineProperty(window, 'GGBApplet', {
    configurable: true,
    get: function () {
      if (!Real) { return undefined; }
      return function (params, b) {
        if (params && typeof params === 'object' &&
            !('showFullscreenButton' in params)) {
          params.showFullscreenButton = true;
        }
        return new Real(params, b);
      };
    },
    set: function (v) { Real = v; }
  });
})();]]>
    </script>
    <xsl:apply-imports/>
  </xsl:template>

  <!-- The applet lives inside an iframe page, and the fullscreen request  -->
  <!-- made by GeoGebra's button is only honoured when the embedding       -->
  <!-- iframe carries the allowfullscreen permission.  This is the core    -->
  <!-- template with that one attribute added.                             -->
  <!-- This is the core template with two attributes added.  Every attribute -->
  <!-- must be written before any content: an <xsl:apply-templates> in a     -->
  <!-- mode that has no matching template falls back to the built-in rule,   -->
  <!-- which copies the element's text into the iframe, and a later          -->
  <!-- <xsl:attribute> then fails with "Cannot add attributes to an element  -->
  <!-- if children have been already added".                                 -->
  <xsl:template match="interactive[@platform]" mode="iframe-interactive">
    <iframe>
      <xsl:attribute name="allowfullscreen"/>
      <xsl:attribute name="allow">
        <xsl:text>fullscreen</xsl:text>
      </xsl:attribute>
      <xsl:apply-templates select="." mode="html-id-attribute"/>
      <xsl:apply-templates select="." mode="interactive-sizing-style-attribute"/>
      <xsl:attribute name="src">
        <xsl:apply-templates select="." mode="iframe-filename"/>
      </xsl:attribute>
      <!-- title attribute for accessibility -->
      <xsl:choose>
        <xsl:when test="not(string(shortdescription) = '')">
          <xsl:attribute name="title">
            <xsl:apply-templates select="shortdescription"/>
          </xsl:attribute>
        </xsl:when>
        <xsl:when test="description">
          <xsl:attribute name="title">
            <xsl:text>described in detail following the image</xsl:text>
          </xsl:attribute>
          <xsl:attribute name="aria-describedby">
            <xsl:apply-templates select="." mode="describedby-id"/>
          </xsl:attribute>
        </xsl:when>
      </xsl:choose>
      <xsl:apply-templates select="." mode="iframe-dark-mode-attribute"/>
    </iframe>
    <!-- possibly give a long description -->
    <xsl:apply-templates select="." mode="description"/>
  </xsl:template>

  <!-- A GeoGebra applet embedded by material id (interactive/@geogebra)   -->
  <!-- is not a slate: the core writes a direct iframe to geogebra.org,   -->
  <!-- so the GGBApplet shim above never sees it.  GeoGebra's iframe URL  -->
  <!-- takes the fullscreen button as the segment sfsb/true, and the      -->
  <!-- request its button makes is only honoured when the iframe carries  -->
  <!-- the allowfullscreen permission.  This is the core template with    -->
  <!-- that URL segment and those two attributes added; the attributes    -->
  <!-- come first, before any applied template adds content.              -->
  <xsl:template match="interactive[@geogebra]" mode="iframe-interactive">
    <xsl:param name="default-aspect" select="'1:1'" />
    <xsl:variable name="ggbToolBar">
      <xsl:choose>
        <xsl:when test="@toolbar='yes'">
          <xsl:text>true</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>false</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="ggbAlgebraInput">
      <xsl:choose>
        <xsl:when test="@algebra-input='yes'">
          <xsl:text>true</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>false</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="ggbResetIcon">
      <xsl:choose>
        <xsl:when test="@reset-icon='yes'">
          <xsl:text>true</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>false</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="ggbShiftDragZoom">
      <xsl:choose>
        <xsl:when test="@shift-drag-zoom='yes'">
          <xsl:text>true</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>false</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="ggbMaterialWidth">
      <xsl:choose>
        <xsl:when test="@material-width">
          <xsl:value-of select="@material-width"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>800</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="aspect-ratio">
      <xsl:apply-templates select="." mode="get-aspect-ratio">
        <xsl:with-param name="default-aspect" select="$default-aspect" />
      </xsl:apply-templates>
    </xsl:variable>
    <xsl:variable name="ggbMaterialHeight">
      <xsl:choose>
        <xsl:when test="@material-height">
          <xsl:value-of select="@material-height"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="round($ggbMaterialWidth div $aspect-ratio)" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <iframe src="https://www.geogebra.org/material/iframe/id/{@geogebra}/scaleContainerClass/interactive-iframe-container/width/{$ggbMaterialWidth}/height/{$ggbMaterialHeight}/allowUpscale/true/autoHeight/true/border/888888/smb/false/stb/{$ggbToolBar}/stbh/{$ggbToolBar}/ai/{$ggbAlgebraInput}/asb/false/sri/{$ggbResetIcon}/rc/false/ld/false/sdz/{$ggbShiftDragZoom}/ctl/false/sfsb/true">
      <xsl:attribute name="allowfullscreen"/>
      <xsl:attribute name="allow">
        <xsl:text>fullscreen</xsl:text>
      </xsl:attribute>
      <xsl:apply-templates select="." mode="html-id-attribute"/>
      <xsl:apply-templates select="." mode="iframe-dark-mode-attribute" />
      <xsl:apply-templates select="." mode="interactive-sizing-style-attribute" />
    </iframe>
  </xsl:template>

</xsl:stylesheet>
