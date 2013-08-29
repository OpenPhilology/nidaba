/* Javascript that deals with the OCR upload, pre-processing, and post-processing */

// Namespacing!
var Iris = {
	Views: {},							// View Objects
	panes: {}							// Instances of view objects
};

Iris.Router = Backbone.Router.extend({
	routes: {
		"": 'main',
		"prescan": 'prescan',			// Step 1: Pre-Scan 
		"preupload": 'preupload',		// Step 2: Pre-Upload
		"upload": 'upload',				// Step 3: Upload
		"metadata": 'metadata',			// Step 4: User-provided Metadata
		"preprocess": 'preprocess',		// Step 5: Information used by OCR Engine
		"status": 'status'				// Step 6: Status information
	}, 
	initialize: function() {
	},
	main: function() {
		this.showPane('body', 'Main');
	},
	prescan: function() {
		this.showPane('#prescan', 'PreScan');
	},
	preupload: function() {
		this.showPane('#preupload', 'PreUpload');
	},
	upload: function() {
		this.showPane('#upload', 'Upload');
	},
	metadata: function() {
		this.showPane('#metadata', 'Metadata');
	},
	preprocess: function() {
		this.showPane('#preprocess', 'PreProcess');
	},
	'status': function() {
		this.showPane('#status', 'Status');
	},
	showPane: function(id, paneName) {

		var that = this;
		$('.pane').hide();

		// Create or show appropriate pane
		if (!Iris.panes[paneName]) {
			Iris.panes[paneName] = new Iris.Views[paneName]({
				el: id
			});
			Iris.panes[paneName].render().$el.show();
		}
		else {
			Iris.panes[paneName].$el.show();
		}

		// Bind app-wide navigation here, since direct route nav skips 'Main'
		$('body').on('click', '.pane .btn', function(e) { that.showNextPane(e) });
		$('body').on('click', '.pane-footer a', function(e) { that.showPrevPane(e) });
		$('body').on('click', '#intro-text .btn', function(e) { that.showNextPane(e) });

		// Don't navigate to main on page load, just display 
		if (paneName != 'Main') {
			$('#intro-text').hide();
			$('#step-progress').show();

			// Determine how many progress bars to fill in
			var steps = ['PreScan', 'PreUpload', 'Upload', 'Metadata', 'PreProcess', 'Status'];
			var completed = steps.indexOf(paneName); 
			for (var i = 0; i < steps.length; i++) {
				if (i < completed)
					$('#step-progress .step-bar').eq(i).addClass('complete');
				else
					$('#step-progress .step-bar').eq(i).removeClass('complete');
			}

			Iris.app.navigate(id, {
				trigger: true
			});
		}
		else {
			$('#step-progress').hide();
			$('#intro-text').show();
		}
	},
	showNextPane: function(e) {
		var currentPane = $(e.target).closest('.pane');
		if (currentPane.length == 0)
			currentPane = $(e.target).closest('#intro-text');	

		var nextPane = currentPane.next('.pane');
		var id = nextPane.attr('id');
		Iris.app.navigate(id, {
			trigger: true
		});
	},
	showPrevPane: function(e) {
		var currentPane = $(e.target).closest('.pane');
		if (!currentPane.length)
			currentPane = $(e.target).closest('#intro-text');	

		var prevPane = currentPane.prev('.pane');
		if (!prevPane.length)
			prevPane = $(e.target).closest('#intro-text');
		var id = prevPane.attr('id');
		Iris.app.navigate(id, {
			trigger: true
		});
	}
});

/* Displays the main, informational section */
Iris.Views.Main = Backbone.View.extend({
	events: {
	},
	initialize: function() {
		console.log("main being initialized");
	},
	render: function() {
		return this;
	}
});

/* Pre-Scan information for user */
Iris.Views.PreScan = Backbone.View.extend({
	events: {
	},
	render: function() {
		$('#step-progress').show();

		return this;
	},
});

Iris.Views.PreUpload = Backbone.View.extend({
	events: {
	},
	render: function() {
		return this;
	},
});

Iris.Views.Upload = Backbone.View.extend({
	events: {
	},
	initialize: function() {
		this.template = '<div class="preview">' + 
							'<span class="img-holder">' + 
							'<img>' + 
							'<span class="uploaded"></span>' +
							'<div class="upload-progress-holder">' +
								'<div class="progress"></div>' +
							'</div>' +
						'</div>';
	},
	render: function() {
		$('#step-progress .step-bar').eq(1).addClass('complete');
		return this;
	},
	createImage: function(file) {
		var preview = $(this.template);
		var image = $(this.template).find('img');

		var reader = new FileReader();

		image.width = 100;
		image.height = 100;

		reader.onload = function(e) {
			image.attr('src', e.target.result);
		};

		reader.readAsDataURL(file);
	}
});

Iris.Views.Metadata = Backbone.View.extend({
	events: {
	},
	render: function() {
		$('#step-progress .step-bar').eq(2).addClass('complete');
		return this;
	},
});

Iris.Views.PreProcess = Backbone.View.extend({
	events: {
	},
	render: function() {
		$('#step-progress .step-bar').eq(3).addClass('complete');
		return this;
	},
});

Iris.Views.Status = Backbone.View.extend({
	events: {
	},
	render: function() {
		$('#step-progress .step-bar').eq(4).addClass('complete');

		return this;
	}
});

$(function() {

	Iris.app = new Iris.Router();
	Iris.hist = Backbone.history.start({
		pushState: true
	});

	// Trigger Bootstrap
	$('#step-progress .step-bar').tooltip();


	window.Iris = Iris; 
});
