<template>
  <div class="modal" id="add-case-modal" tabindex="-1" role="dialog" @click.stop>
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" v-if="this.case && this.case.name">{{ this.case.name }}</h5>
          <h5 class="modal-title" v-else>ADD CASELAW</h5>
          <button type="button" @click.stop="closeModal" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.stop.prevent id="form-search-cap" v-if="!(this.case && typeof(this.case.id) === 'number')">
            <h6>Search CAP</h6>
            <div id="field-group-search">
              <input v-model="searchText" id="field-search-cap" :placeholder="'Enter '+ extraFields.cap.value"
                     class="form-control">
              <span>Search using:</span>
              <v-select :options="['Name abbreviation', 'Citation', 'Text search']"
                        v-model="extraFields.cap.value"
                        :clearable="false"
                        placeholder="search">
              </v-select>

              <span class="button-container">
                <search-button :showLoading="showLoading"></search-button>
              </span>
            </div>
            <ul v-if="searchResults.length" class="results-list">
              <div v-for="result in searchResults" @click="autofillCase(result)"
                   class="result-container"
                   :class="chosenCase.id === result.id ? 'chosen' : ''"
                   :key="result.id">
                <case-result :result="result">
                </case-result>
              </div>
            </ul>
            <ul v-if="showNoSearchResults" class="results-list">
              <li class="result-container p-2">No results found</li>
            </ul>
            <hr>
          </form>
          <form @submit.stop id="form-add-case">

            <!-- search results -->
            <div class="form-label-group" id="field-group-url">
              <input v-model="newCase.url" id="field-url" placeholder="URL" class="form-control">
              <label for="field-url">URL</label>
            </div>
            <div class="form-label-group" id="field-group-citation">
              <input v-model="newCase.citation" id="field-citation" placeholder="Citation" class="form-control">
              <label for="field-citation">Citation</label>
            </div>
            <div class="form-label-group" id="field-group-name">
              <input v-model="newCase.name" id="field-name" placeholder="Case name" required class="form-control">
              <label for="field-name">Case name</label>
            </div>
            <div class="form-label-group" id="field-group-short">
              <textarea v-model="newCase.short_description" id="field-short-description" placeholder="SHORT DESCRIPTION"
                        class="form-control"></textarea>
            </div>
            <div class="form-label-group" id="field-group-date">
              <input v-model="newCase.decision_date" id="field-decision-date" placeholder="DECISION DATE" type="date"
                     required
                     class="form-control">
              <label for="field-decision-date">DECISION DATE</label>
            </div>
            <div class="form-label-group" id="field-group-long">
            <textarea v-model="newCase.long_description" id="field-long-description" placeholder="LONGER DESCRIPTION"
                      class="form-control"></textarea>
            </div>
            <v-select transition=""
                      id="field-group-jurisdiction"
                      label="jurisdiction"
                      placeholder="Jurisdiction"
                      :options="choices.jurisdictions"
                      @input="chooseJurisdiction"
                      v-model="newCase.jurisdiction">
            </v-select>

            <v-select transition=""
                      id="field-group-court"
                      label="courtName"
                      placeholder="Court"
                      :options="choices.courts"
                      v-model="newCase.court">
            </v-select>

            <v-select transition=""
                      class="color-dropdown"
                      label="color"
                      placeholder="Border color"
                      :filterable="false"
                      :clearable="false"
                      @input="setSelected"
                      v-model="newCase.color"
                      :options="colors">
              <template #selected-option="{ color }">
                <span :style="{backgroundColor: color}" class="color-square">
                  {{ color }}
                </span>
              </template>
              <template #option="{ color }">
                <span :style="{backgroundColor: color}" class="color-square">
                  {{ color }}
                </span>
              </template>
            </v-select>
            <v-select multiple
                      id="field-group-categories"
                      :filterable="false"
                      transition=""
                      label="name"
                      v-model="newCase.categories"
                      placeholder="Categories"
                      :options="$store.state.categories">
              <template #selected-option="{ color, shape, name }">
                <shape-component :width="20" :color="color" :shapetype="shape"></shape-component>
                <span v-text="name"></span>
              </template>
              <template #option="{ color, shape, name }">
                <shape-component :width="28" :color="color" :shapetype="shape"></shape-component>
                <span v-text="name"></span>
              </template>
            </v-select>
          </form>
          <div v-if="errors.length" class="form-errors p-2 mt-2 small">
            <b>Please correct the following error(s):</b>
            <ul class="m-0 list-inline">
              <li class="list-inline-item" v-for="error in errors" v-bind:key="error">{{ error }}</li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-tertiary" @click.stop="closeModal" data-dismiss="modal">
            Cancel
          </button>
          <template v-if="this.case && this.case.name">
            <button type="button" class="btn btn-primary" @click="deleteCase" data-dismiss="modal">
              Delete
            </button>
            <button type="button" class="btn btn-primary" @click.stop="updateCase"
                    data-dismiss='modal'>
              Update
            </button>
          </template>
          <template v-else>
            <button type="button" class="btn btn-primary btn-highlight" @click.stop="addCase"
                    data-dismiss="modal">
              ADD
            </button>
          </template>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import axios from "axios";
import store from "./store";
import vSelect from 'vue-select';
import CaseResult from '../../search/case-result.vue';
import SearchButton from '../../vue-shared/search-button';
import ShapeComponent from './shape-component';

export default {
  name: "add-case-modal",
  components: {
    vSelect,
    CaseResult,
    SearchButton,
    ShapeComponent,
  },
  props: [
    'shown',
    'modal',
    'case'
  ],
  data() {
    return {
      choices: {},
      searchResults: [],
      showNoSearchResults: false,
      searchText: '',
      chosenCase: {},
      newCase: {},
      errors: [],
      colors: [],
      extraFields: { // need more info to interact with dropdown fields
        cap: {
          name: 'search by',
          label: 'Name abbreviation',
          value: 'Name abbreviation'
        }
      },
      showLoading: false,
      categories: []
    }
  },
  methods: {
    checkForm() {
      this.errors = [];
      if (!this.newCase.name) {
        this.errors.push('Case name is required.');
      }
      if (!this.newCase.decision_date) {
        this.errors.push('Decision date is required.');
      }
      if (this.newCase.url && !this.checkUrl(this.newCase.url)) {
        if (!/^https?:\/\//i.test(this.newCase.url) && this.checkUrl('https://' + this.newCase.url)) {
            this.newCase.url = 'https://' + this.newCase.url;
        } else {
          this.errors.push('URL is not valid.')
        }
      }
    },
    closeModal() {
      this.$parent.closeModal();
      this.setupCase()
    },
    updateCase() {
      this.checkForm();
      if (this.errors.length) return;
      let caselaw = this.unbind(this.newCase)

      if (!caselaw.jurisdiction)
        caselaw.jurisdiction = ''

      if (!caselaw.court)
        caselaw.court = ''

      // only save category ids
      caselaw.categories = caselaw.categories.map(category => category.id)
      store.commit('updateCase', caselaw)
      this.closeModal()
    },
    addCase() {
      this.checkForm();
      if (this.errors.length) return;
      let caselaw = this.unbind(this.newCase)
      // only save category ids
      caselaw.categories = caselaw.categories.map(category => category.id)
      store.commit('addCase', caselaw);
      this.closeModal();
    },
    deleteCase() {
      store.commit('deleteCase', this.case.id);
      this.closeModal();
    },
    chooseCase(result) {
      // choosing case from CAP search
      this.chosenCase = result;
    },
    setSelected(color) {
      this.newCase.color = color
    },

    formatDate(date) {
      // autofill missing month and day. Not ideal, but this is a timeline, after all.
      let date_parts = date.split("-");
      let year = date_parts[0];
      let day = date_parts.length === 3 ? date_parts[2] : "01";
      let month = date_parts.length >= 2 ? date_parts[1] : "01";
      return year + "-" + month + "-" + day;
    },
    autofillCase(result) {
      this.chosenCase = result;
      this.newCase.name = this.chosenCase.name_abbreviation;
      this.newCase.citation = this.chosenCase.citations[0].cite;
      this.newCase.url = this.chosenCase.frontend_url;
      this.newCase.decision_date = this.formatDate(this.chosenCase.decision_date);
      this.newCase.jurisdiction = this.chosenCase.jurisdiction.name_long
      this.newCase.court = this.chosenCase.court.name
    },
    searchCAP() {
      this.showNoSearchResults = false
      if (this.searchText) {
        this.showLoading = true;

        let query;
        if (this.extraFields.cap.value === 'Citation') {
          query = 'cite'
        } else if (this.extraFields.cap.value === 'Name abbreviation') {
          query = 'name_abbreviation'
        } else {
          query = 'search'
        }
        let url = store.state.urls.api_root + "cases?" + query + "=" + this.searchText;
        axios.get(url)
            .then(response => response.data)
            .then(searchResponse => {
              this.searchResults = searchResponse.results;
              if (this.searchResults.length === 0) {
                this.showNoSearchResults = true
              }
              this.showLoading = false;
            })
      }
    },
    valueUpdated() {
      this.searchCAP()
    },
    clearContent() {
      this.closeModal();
      this.setupCase();
    },
    unbind(obj) {
      return JSON.parse(JSON.stringify(obj))
    },
    hydrateCategories(categories = []) {
      let hydratedCats = [];
      for (let i = 0; i < categories.length; i++) {
        let cat = store.getters.category(categories[i])
        if (cat)
          hydratedCats.push(cat)
      }
      return hydratedCats
    },
    setupCase(existingCase) {
      this.newCase = existingCase ? this.unbind(this.case) : this.unbind(store.getters.templateCase);
      this.newCase.categories = this.hydrateCategories(this.newCase.categories)
    },
    chooseJurisdiction(jur) {
      if (jur)
        this.newCase.jurisdiction = jur
      this.newCase = this.unbind(this.newCase)
    },
    chooseCourt(court) {
      if (court)
        this.newCase.court = court.courtName
      this.newCase = this.unbind(this.newCase)
    },
    checkUrl(url) {
      try {
        new URL(url);
      } catch (e) {
        return false;
      }
      return url.includes('.');
    }
  },
  watch: {
    case(existingCase) {
      this.setupCase(existingCase)
    }
  },
  beforeMount() {
    this.colors = store.getters.choices.colors;
    this.choices = store.getters.choices;
    this.categories = store.getters.categories;
    this.setupCase(this.case)
  },
}
</script>