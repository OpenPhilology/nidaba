<xsl:stylesheet version="1.0" xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
	<xsl:strip-space elements="*"/>
	<xsl:template match="/">
	<div class='row'>
		<div class='col-md-6'>
			<xsl:apply-templates select=".//tei:graphic"/>
		</div>
		<div class='col-md-6'>
			<xsl:for-each select=".//tei:line">
				<span>
				<xsl:for-each select=".//tei:zone[@type='segment']">
					<xsl:value-of select="concat(.,'&#160;')"/>
				</xsl:for-each>
				</span><br/>
			</xsl:for-each>
		</div>
	</div>
	</xsl:template>
	<xsl:template match="tei:graphic">
		<img style='width:100%' src="{@url}"/>
	</xsl:template>
</xsl:stylesheet>

