<?xml version="1.0" encoding="UTF-8"?>
<!-- Custom LaTeX/PDF conversion: render <exercises> divisions (homework) without a number -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:import href="./core/pretext-latex.xsl"/>

  <xsl:template match="exercises" mode="serial-number"/>
  <xsl:template match="exercises" mode="number"/>

  <!-- The surface-flux Parsons concept check prints its cards in a        -->
  <!-- scrambled order (block/@order), and PreTeXt's static version would  -->
  <!-- add a Solution listing them in the solved order, which is the       -->
  <!-- worked computation a skeletal PDF leaves to the student. Leave out  -->
  <!-- that Solution and its separator for this one exercise.              -->
  <!-- The same holds for the two checks added after it: the true/false   -->
  <!-- claim about the area element of a graph (its static version prints -->
  <!-- "True." and the derivation) and the card-ordering check on the     -->
  <!-- tilt of the surface.                                               -->
  <xsl:template match="exercise[@xml:id = 'check-flux-param-parsons'
                                or @xml:id = 'check-graph-area-element-tf'
                                or @xml:id = 'check-surface-tilt-parsons']" mode="present-exercise-solutions"/>
  <xsl:template match="exercise[@xml:id = 'check-flux-param-parsons'
                                or @xml:id = 'check-graph-area-element-tf'
                                or @xml:id = 'check-surface-tilt-parsons']" mode="exercise-component-separator"/>
</xsl:stylesheet>
