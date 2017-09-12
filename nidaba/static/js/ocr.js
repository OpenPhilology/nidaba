/* Javascript that deals with the OCR upload, pre-processing, and post-processing */

// Namespacing!
var Iris = {
	Views: {},							// View Objects
	panes: {}							// Instances of view objects

};

Iris.Task = Backbone.Model.extend();
Iris.Tasks = Backbone.Collection.extend({
	initialize: function(models, args) {
		this.url = function() { return args.batch_url() + '/tasks'; };
	},
	model: Iris.Task
});

Iris.Doc = Backbone.Model.extend();
Iris.Docs = Backbone.Collection.extend({
	initialize: function(models, args) {
		this.url = function() { return args.batch_url() + '/pages'; };
	},
	model: Iris.Doc
});

Iris.Batch = Backbone.Model.extend({
	initialize: function() {
		this.docs = new Iris.Docs([], {batch_url: this.url.bind(this)});
		this.tasks = new Iris.Tasks([], {batch_url: this.url.bind(this)});
		this.metadata = {};
		this.metadata_url;
		this.metadata_complete = 0;
		this.upload_complete = 0;
	},
	urlRoot: '/api/v1/batch',
	// backbone isn't really compatible with a model just being a file on
	// the server.
	save_metadata: function() {
		data = YAML.stringify(this.metadata);
		form_data = new FormData;
		blob = new Blob([data])
		form_data.append('scans', blob, 'metadata.yaml');
		var that = this;
		return $.ajax({
			url: this.url() + '/pages?auxiliary=1',
			data: form_data,
			processData: false,
			contentType: false,
			type: 'POST',
			success: function(data) {
				that.metadata_url = data[0]['url'];
			}
		});
	},
	// adds a task to the current batch. XXX: manage tasks using backbone
	// methods.
	add_task: function(group, task, args) {
		var that = this;
		return $.ajax({
			url: this.url() + '/tasks/' + group + '/' + task,
			data: JSON.stringify(args),
			contentType: "application/json",
			dataType: 'json',
			type: 'POST',
			success: function() {
				// sync task list
				that.tasks.fetch();
			},
		});
	},
	// execute the batch.
	execute: function() {
		return $.ajax({
			url: this.url(),
			type: 'POST'
		});
	}
});

Iris.Router = Backbone.Router.extend({
	routes: {
		"": 'main',
		"prescan": 'prescan',			// Step 1: Pre-Scan 
		"preupload": 'preupload',		// Step 2: Pre-Upload
		"upload(/:id)": 'upload',			// Step 3: Upload
		"metadata/:id": 'metadata',		// Step 4: User-provided Metadata
		"preprocess/:id": 'preprocess',		// Step 5: Information used by OCR Engine
		"status/:id": 'status'			// Step 6: Status information
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
	upload: function(id) {
		if(!id) {
			Iris.batch.save(null, {
				success: function (model, response) {
					Iris.app.navigate('#upload/'+model.id, {replace: true});
				},
				error: function (model, response) {
					new Bootstrap.alert({ el: $('#page') }).render(response, 'error');
				}
			});
		}
		this.showPane('#upload', 'Upload');
	},
	metadata: function(id) {
		this.showPane('#metadata', 'Metadata');
	},
	preprocess: function(id) {
		this.showPane('#preprocess', 'PreProcess');
	},
	'status': function(id) {
		Iris.batch = new Iris.Batch({id: id});
		Iris.batch.fetch();
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
		$('body').on('click', '.pane-footer button', function(e) { that.showNextPane(e) });
		$('body').on('click', '.pane-footer a', function(e) { that.showPrevPane(e) });
		$('body').on('click', '#intro-text .btn', function(e) { that.showNextPane(e) });

		// Set selected value as text of dropdown
		$('body').on('click', '.dropdown-menu li a', function(){
			var selText = $(this).text();
			$(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
		});

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
		// everything after preupload is stateful and requires a batch id.
		if(Iris.batch.id && id != 'prescan' && id != 'preupload') {
			Iris.app.navigate('#' + id + '/' + Iris.batch.id, {trigger: true});
		} else {
			Iris.app.navigate(id, {trigger: true});
		}
	},
	showPrevPane: function(e) {
		var currentPane = $(e.target).closest('.pane');
		if (!currentPane.length)
			currentPane = $(e.target).closest('#intro-text');	

		var prevPane = currentPane.prev('.pane');
		if (!prevPane.length)
			prevPane = $(e.target).closest('#intro-text');
		var id = prevPane.attr('id');
		// everything after preupload is stateful and requires a batch id.
		if(Iris.batch.id && id != 'prescan' && id != 'preupload') {
			Iris.app.navigate('#' + id + '/' + Iris.batch.id, {trigger: true});
		} else {
			Iris.app.navigate(id, {trigger: true});
		}
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
		this.listenTo(Iris.batch, "change", this.render);
		Iris.batch.dropzone = this.$el.find('#upload-area').dropzone({
			paramName: 'scans',
			acceptedFiles: 'image/*',
			autoProcessQueue: false,
			url: function(files) { return '/api/v1/batch/' + Iris.batch.id + '/pages'; },
			init: function () {
				$('#submit-scans').prop('disabled', true);
			        dz = this;
				$('#submit-scans').on("click", function() {
					dz.processQueue(); 
				});
				this.on("addedfile", function(file) {
					Iris.batch.upload_complete = 0;
					$('#submit-scans').prop('disabled', false);
				});
				this.on("complete", function(file) {
					this.removeFile(file);
				});
				this.on("totaluploadprogress", function(uploadProgress) {
					if (uploadProgress > 0) {
						$("#upload-progress").css("width", uploadProgress + '%');
					}
				});
				this.on("queuecomplete", function() {
					Iris.batch.upload_complete = 1;
					if (Iris.batch.metadata_complete) {
						$('#submit-metadata').removeAttr('disabled');
					} else {
						$('#submit-metadata').prop('disabled', true);
					}
					Iris.batch.docs.fetch();
				});
			}
		});
	},
	render: function() {
		$('#step-progress .step-bar').eq(1).addClass('complete');
		return this;
	},
	showMessage: function(message) {
		this.$el.find('#upload-area .message').html(message);
	}
});

Iris.Views.Metadata = Backbone.View.extend({
	events: {
	},
	initialize: function() {
		this.listenTo(Iris.batch, 'change', this.render);
	},
	render: function() {
		$('#step-progress .step-bar').eq(2).addClass('complete');
		$('#submit-metadata').prop('disabled', true);
		// only enable the next step button if the form is complete.
		$('#metadata-form').change(function() {
			var empty = false;
			$('#metadata-form input').each(function() {
				if($(this).val() == '') {
					empty = true;
				}
				var name = $(this).attr('name');

				// I'm sure there is an entirely obvious way to
				// write this that just doesn't fit into my
				// puny C programmer mind.
				if($(this).attr('type') == 'radio') {
					sel = $("input:radio[name='" + name + "']:checked");
					if(sel.length > 0) {
						Iris.batch.metadata[name] = sel.val();
					} else {
						empty = true;
					}
				} else {
					Iris.batch.metadata[name] = $(this).val()
				}
			});
			Iris.batch.metadata_complete = !empty;
			if (Iris.batch.metadata_complete && Iris.batch.upload_complete) {
				$('#submit-metadata').removeAttr('disabled');
			} else {
				$('#submit-metadata').prop('disabled', true);
			}
		});

		$('#submit-metadata').on('click', function(e) {
			Iris.batch.save_metadata();
		});
		return this;
	},
});

Iris.Views.PreProcess = Backbone.View.extend({
	events: {
	},
	initialize: function() {
		this.listenTo(Iris.batch, 'change', this.render);
	},
	render: function() {
		$('#step-progress .step-bar').eq(3).addClass('complete');
		$('#submit-batch').prop('disabled', true);
		// language selector/script
		var checked_opts = 0;
		var blacklisted_scripts = false;
		var show_greek_fonts = false;
		var show_arab_fonts = false;
		var show_syr_fonts = false;

		$('#languages').multiselect({
			onChange: function(option, checked) {
				show_greek_fonts = false;
				show_arab_fonts = false;
				show_syr_fonts = false;

				// font selection enabler/disabler
				lang_whitelist = ['lat', 'eng', 'grc'];
				var sel = $.map($('#languages option:selected'), function(e) { return e.value; });
				if(sel.includes('grc') && !sel.some(val => lang_whitelist.indexOf(val) === -1)) {
					$('#greek-fonts').show();
					blacklisted_scripts = false;
				} else {
					blacklisted_scripts = true;
					$('#greek-fonts').hide();
				}
				if(sel.length == 1 && sel.includes('ara')) {
					blacklisted_scripts = false;
					show_arab_fonts = true;
					$('#arabic-fonts').show();
				} else {
					blacklisted_scripts = true;
					$('#arabic-fonts').hide();
				}
				if(sel.length == 1 && sel.includes('syr')) {
					blacklisted_scripts = false;
					show_syr_fonts = true;
					$('#syriac-fonts').show();
				} else {
					blacklisted_scripts = true;
					$('#syriac-fonts').hide();
				}

				// submit button enabler/disabler
				if(checked) {
					checked_opts += 1;
				} else if(checked_opts) {
					checked_opts -= 1;
				}

				if(checked_opts) {
					$('#submit-batch').removeAttr('disabled');			
				} else {
					$('#submit-batch').prop('disabled', true);
				}
			}
		});
		$('#submit-batch').on('click', function(e) {
			console.log('submitting batch');
			if(Iris.batch.tasks.length == 0) {
				var def = [];
				def.push(Iris.batch.add_task('img', 'any_to_png', {}));
				def.push(Iris.batch.add_task('binarize', 'nlbin', {threshold: 0.5,
									  zoom: 0.5, 
									  escale: 1.0, 
									  border: 0.1, 
									  perc: 80, 
									  range: 20, 
									  low: 5, 
									  high: 90}));
				def.push(Iris.batch.add_task('segmentation', 'tesseract', {}));
				var gr_font = $("input[type='radio'][name='greek-font']:checked");
				var ara_font = $("input[type='radio'][name='arabic-font']:checked");
				var syr_font = $("input[type='radio'][name='syriac-font']:checked");

				if(show_greek_fonts && !blacklisted_scripts && gr_font.val() != 'none') {
					def.push(Iris.batch.add_task('ocr', 'kraken', {model: gr_font.val()}));
				} else if(show_arab_fonts && !blacklisted_scripts && ara_font.val() != 'none') {
					def.push(Iris.batch.add_task('ocr', 'kraken', {model: ara_font.val()}));
				} else if(show_syr_fonts && !blacklisted_scripts && syr_font.val() != 'none') {
					def.push(Iris.batch.add_task('ocr', 'kraken', {model: syr_font.val()}));
				} else {
					var langs = []
					$('#languages option:selected').each(function(idx, sel) {
						langs.push(sel.value);
					});
					def.push(Iris.batch.add_task('ocr', 'tesseract', {languages: langs, extended: true}));
				}
				def.push(Iris.batch.add_task('output', 'metadata', {metadata: Iris.batch.metadata_url, validate: false}));
				def.push(Iris.batch.add_task('archive', 'pybossa', {name: Iris.batch.metadata['title'], 
									   description: Iris.batch.metadata['notes']}));
				$.when.apply(null, def).done(function() { Iris.batch.execute() });
			}
		});
		return this;
	},
});

Iris.Views.Status = Backbone.View.extend({
	events: {
	},
	initialize: function() {
		this.listenTo(Iris.batch, 'change', this.render);
	},
	render: function() {
		$('#step-progress .step-bar').eq(4).addClass('complete');
		if(!Iris.fetch_interval_id) {
			Iris.fetch_interval_id = setInterval(function() {
				Iris.batch.fetch();
			}, 5000);
		}

		if(Iris.batch.attributes['chains']) {
			var done = 0;
			var running = 0;
			var tasks = 0;
			$('#task-output').empty();
			$('#task-errors').empty();
			$.each(Iris.batch.attributes['chains'], function(i, value) {
				tasks += 1;
				if(value['state'] === 'SUCCESS') {
					done += 1;
				} else if(value['state'] === 'RUNNING') {
					running += 1;
				} else if(value['state'] === 'FAILURE') {
					alert = $('<a>').attr('class', 'list-group-item list-group-item-success')
							.attr('href', value['root_documents'])
							.text(value['errors'][value['errors'].length - 2]);
					$('#task-errors').append(alert);
				}
				// leaf nodes are results
				if(!value['children'].length) {
					var res = [];
					value['root_documents'].sort();
					for (var i = 0; i < value['root_documents'].length; i++) {
						var rd = _.last(value['root_documents'][i].split('/'));
						res.push($('<a>').attr('class', 'list-group-item clearfix')
							      .text(rd));
						var file_buttons = $('<span>').attr('class', 'pull-right');
						if(value['result']) {
							value['result'].sort();
							res[i].attr('href', value['result'][i]);
							res[i].on('click', function(e) {
								e.preventDefault();
								$.get(this.href, function(data) {
									var fragment = Iris.xsltProcessor.transformToFragment(data, document);
									Iris.fragment = fragment;
									$('#tei_modal_content').replaceWith(fragment);
									$('#tei_modal').modal('show');
								});
							});
							var link_el = $('<a>').attr('href', value['result'][i])
									      .attr('class', 'btn btn-xs btn-success')
									      .attr('download', _.last(value['result'][i].split('/')));
							link_el.append($('<span>').attr('class', 'glyphicon glyphicon-save'));
							link_el.on('click', function(e) {
								e.stopPropagation();
							});

							file_buttons.append(link_el);
						}
						// look for failures up the chain and
						// reduce expected task count
						// correspondingly. Also add a failure
						// glyphicon. 
						parent = value;
						var parent_counter = 1;
						while(parent) {
							if(parent['state'] == 'FAILURE') {
								file_buttons.append($('<span>').attr('class', 'glyphicon glyphicon-remove'));
								tasks -= parent_counter;
							}
							parent_counter++;
							if(!parent['parents']) {
								break;
							}
							parent = parent['parents'][0];
						}
						res[i].append(file_buttons);
					}
					$('#task-output').append(res);
				}
			});
			// sort output names lexicographically
			$results = $('#task-output').children('a');
			$results.sort(function(a, b) {
				return a.text.localeCompare(b.text);
			});
			$results.detach().appendTo('#task-output');

			$("#tasks-done").css("width", (done/tasks)*100 + '%');
			$("#tasks-progress").css("width",  (running/tasks)*100 + '%');
			// everything is done so don't check state periodically anymore.
			if(tasks == done) {
				clearInterval(Iris.fetch_interval_id);
			}
		}
		return this;
	}
});

$(function() {
	Iris.app = new Iris.Router();
	Iris.batch = new Iris.Batch();
	Iris.hist = Backbone.history.start({pushState: true});

	// Trigger Bootstrap
	$('#step-progress .step-bar').tooltip();

	$.get($('#tei_stylesheet').attr('href'), '', function(data) {
		Iris.xsltProcessor = new XSLTProcessor();
		Iris.xsltProcessor.importStylesheet(data);
	});

	window.Iris = Iris; 
});
