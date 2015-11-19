<xsl:stylesheet version="1.0" xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
	<xsl:variable name="api_root" select="'/api/v1'"/>	
	<xsl:template match="/">
		<xsl:apply-templates select=".//tei:graphic"/>
		<div>
		<xsl:for-each select=".//tei:line">
			<xsl:value-of select="concat(.,'&#xA;')"/>
		</xsl:for-each>
		</div>
	</xsl:template>
	<xsl:template match="tei:graphic">
		<img src="{$api_root}/{@url}"/>
	</xsl:template>
</xsl:stylesheet>

